// Sends raw MIDI bytes to a CoreMIDI destination, with optional pauses.
// usage: midisend <destination-substring> <item>...
//   item = hex bytes of one message ("903c64"), or "sleep:<ms>"
import CoreMIDI
import Foundation

func fail(_ s: String) -> Never { FileHandle.standardError.write((s + "\n").data(using: .utf8)!); exit(1) }

let args = CommandLine.arguments
if args.count < 3 { fail("usage: midisend <destination-substring> <hexbytes|sleep:ms>...") }
let sub = args[1].lowercased()

var client = MIDIClientRef()
if MIDIClientCreate("midisend" as CFString, nil, nil, &client) != 0 { fail("MIDIClientCreate") }
var port = MIDIPortRef()
if MIDIOutputPortCreate(client, "out" as CFString, &port) != 0 { fail("MIDIOutputPortCreate") }

var dest: MIDIEndpointRef = 0
for i in 0..<MIDIGetNumberOfDestinations() {
    let ep = MIDIGetDestination(i)
    var name: Unmanaged<CFString>?
    MIDIObjectGetStringProperty(ep, kMIDIPropertyDisplayName, &name)
    if let n = name?.takeRetainedValue() as String?, n.lowercased().contains(sub) { dest = ep; break }
}
if dest == 0 { fail("no destination matching \(sub)") }

for item in args.dropFirst(2) {
    if item.hasPrefix("sleep:") { usleep(UInt32(item.dropFirst(6))! * 1000); continue }
    var bytes: [UInt8] = []
    var s = Substring(item)
    while s.count >= 2 { bytes.append(UInt8(s.prefix(2), radix: 16)!); s = s.dropFirst(2) }
    var list = MIDIPacketList()
    let pkt = MIDIPacketListInit(&list)
    _ = MIDIPacketListAdd(&list, MemoryLayout<MIDIPacketList>.size, pkt, 0, bytes.count, bytes)
    if MIDISend(port, dest, &list) != 0 { fail("MIDISend") }
    usleep(2000)
}
usleep(20000)
