// Backs up the Pulse 2's sounds the way SynthEdit backs up a bank: one "NNN Name.syx" per sound and a
// "Patches.txt" index, in a folder of the caller's choosing (iCloud Drive/Patches/Pulse2, beside the other synths). READ-ONLY on the instrument: it only
// sends sound REQUESTS. (A sound DUMP sent to the instrument with a slot number is stored to that slot.)
//
// usage: p2dump <port-substring> <out-folder> [first] [last]      P001..P500 as the display numbers them (default all);
//        "edit" = the edit buffer. The request itself counts from 0: P001 is sound 0.
import CoreMIDI
import Foundation

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

let args = CommandLine.arguments
if args.count < 3 { fail("usage: p2dump <port-substring> <out-folder> [first|edit] [last]") }
let sub = args[1].lowercased()
let folder = args[2]
let editBuffer = (args.count > 3) && (args[3] == "edit")
let first = editBuffer ? 1 : ((args.count > 3) ? Int(args[3])! : 1)
let last = editBuffer ? 1 : ((args.count > 4) ? Int(args[4])! : 500)

let kHeader: [UInt8] = [0xF0, 0x3E, 0x16]
let kDeviceBroadcast: UInt8 = 0x7F
let kSoundRequest: UInt8 = 0x00
let kSoundDump: UInt8 = 0x10
let kDumpLength = 137
let kNameOffset = 113, kNameLength = 14

func endpoint(_ count: Int, _ get: (Int) -> MIDIEndpointRef) -> MIDIEndpointRef {
    for i in 0..<count {
        let ep = get(i)
        var name: Unmanaged<CFString>?
        MIDIObjectGetStringProperty(ep, kMIDIPropertyDisplayName, &name)
        if let n = name?.takeRetainedValue() as String?, n.lowercased().contains(sub) { return ep }
    }
    return 0
}

var client = MIDIClientRef()
if MIDIClientCreate("p2dump" as CFString, nil, nil, &client) != 0 { fail("MIDIClientCreate") }
var outPort = MIDIPortRef()
if MIDIOutputPortCreate(client, "out" as CFString, &outPort) != 0 { fail("MIDIOutputPortCreate") }
let dest = endpoint(MIDIGetNumberOfDestinations(), { MIDIGetDestination($0) })
let source = endpoint(MIDIGetNumberOfSources(), { MIDIGetSource($0) })
if dest == 0 || source == 0 { fail("no MIDI port matching \(sub)") }

// Incoming SysEx, reassembled across packets; complete messages go on a queue the main loop waits on.
let lock = NSCondition()
var assembling: [UInt8] = []
var received: [[UInt8]] = []

var inPort = MIDIPortRef()
let status = MIDIInputPortCreateWithBlock(client, "in" as CFString, &inPort) { list, _ in
    var packet = list.pointee.packet
    for _ in 0..<list.pointee.numPackets {
        let bytes = withUnsafeBytes(of: packet.data) { Array($0.prefix(Int(packet.length))) }
        lock.lock()
        for b in bytes {
            if b == 0xF0 { assembling = [b] } else if !assembling.isEmpty {
                assembling.append(b)
                if b == 0xF7 { received.append(assembling); assembling = []; lock.signal() }
            }
        }
        lock.unlock()
        packet = MIDIPacketNext(&packet).pointee
    }
}
if status != 0 { fail("MIDIInputPortCreateWithBlock") }
MIDIPortConnectSource(inPort, source, nil)

func send(_ bytes: [UInt8]) {
    var list = MIDIPacketList()
    let pkt = MIDIPacketListInit(&list)
    _ = MIDIPacketListAdd(&list, MemoryLayout<MIDIPacketList>.size, pkt, 0, bytes.count, bytes)
    MIDISend(outPort, dest, &list)
}

func waitForDump(timeout: TimeInterval) -> [UInt8]? {
    let deadline = Date().addingTimeInterval(timeout)
    lock.lock()
    defer { lock.unlock() }
    while true {
        if let i = received.firstIndex(where: { $0.count == kDumpLength && $0[4] == kSoundDump }) {
            let m = received.remove(at: i)
            return m
        }
        if !lock.wait(until: deadline) { return nil }
    }
}

func checksumOK(_ m: [UInt8]) -> Bool {
    let sum = m[1..<(kDumpLength - 2)].reduce(0) { $0 + Int($1) } & 0x7F
    return sum == Int(m[kDumpLength - 2])
}

func soundName(_ m: [UInt8]) -> String {
    let data = Array(m[7..<(7 + 128)])
    let chars = data[kNameOffset..<(kNameOffset + kNameLength)].map { (32...126).contains($0) ? Character(UnicodeScalar($0)) : " " }
    return String(chars).trimmingCharacters(in: .whitespaces)
}

func fileSafe(_ s: String) -> String {
    String(s.map { "/:\\".contains($0) ? "-" : $0 })
}

try? FileManager.default.createDirectory(atPath: folder, withIntermediateDirectories: true)
let indexPath = folder + "/Patches.txt"
var index = ""      // "NNN  Name" per line, as the Voyager's Patches.txt beside it
var got = 0, missing = 0

for n in first...last {
    let sound = n - 1                    // the display's P001 is the request's sound 0
    let bank = editBuffer ? UInt8(0x7F) : UInt8(sound >> 7)
    let prog = editBuffer ? UInt8(0x00) : UInt8(sound & 0x7F)
    lock.lock(); received.removeAll(); lock.unlock()
    send(kHeader + [kDeviceBroadcast, kSoundRequest, bank, prog, 0xF7])
    guard let m = waitForDump(timeout: 1.5) else {
        missing += 1
        print(String(format: "%03d  (no reply)", n))
        continue
    }
    if !checksumOK(m) { print(String(format: "%03d  checksum mismatch - kept anyway", n)) }
    let name = soundName(m)
    let label = editBuffer ? "edit" : String(format: "%03d", n)
    let file = "\(folder)/\(label) \(fileSafe(name.isEmpty ? "unnamed" : name)).syx"
    FileManager.default.createFile(atPath: file, contents: Data(m))
    index += "\(label)  \(name)\n"
    got += 1
    if got % 50 == 0 { print("\(got) received...") }
    usleep(30_000)   // pacing: one request in flight, a short breather after each reply
}
try? index.write(toFile: indexPath, atomically: true, encoding: .utf8)
print("received \(got), missing \(missing); index \(indexPath)")
