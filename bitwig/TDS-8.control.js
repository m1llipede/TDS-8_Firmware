// TDS-8 Digital Scribble Strip: Bitwig Studio controller script
//
// Sends Bitwig track names and the selected track to the TDS-8 Bridge app over
// OSC, so the TDS-8 OLEDs show your Bitwig tracks the same way they show
// Ableton tracks. No firmware change and no Bridge change is needed: the Bridge
// already accepts these messages.
//
//   Bitwig  -> Bridge  (UDP 127.0.0.1:8003)
//     /trackname   <index 0-31> <name>   one per track, sent on every rename
//     /activetrack <index 0-31>          the track selected in Bitwig
//     /hi                                heartbeat, shows "Connected" in the Bridge
//
//   Bridge  -> Bitwig  (UDP port 8001, this script listens there)
//     /request-trackname <index>         Bridge "Refresh" asks for one name
//     /reannounce                        resend everything
//     /hello                             Bridge handshake, answered with /hi
//
// Install: copy this file into
//   Windows  Documents\Bitwig Studio\Controller Scripts\
//   macOS    ~/Documents/Bitwig Studio/Controller Scripts/
// then Settings > Controllers > Add controller > PlayOptix > TDS-8.

loadAPI(18);

host.defineController("PlayOptix", "TDS-8", "1.0", "B2B207D4-7841-46F5-B658-15C110055E42", "PlayOptix");
host.defineMidiPorts(0, 0);

var NUM_TRACKS = 32;          // 4 TDS-8 units x 8 displays
var HEARTBEAT_MS = 5000;

var bridge = null;            // OscConnection to the Bridge
var trackBank = null;
var names = [];
var selectedIndex = -1;
var bridgeHost, sendPort, listenPort;

function init() {
   var prefs = host.getPreferences();
   bridgeHost = prefs.getStringSetting("Bridge address", "TDS-8 Bridge", 32, "127.0.0.1");
   sendPort   = prefs.getNumberSetting("Bridge listen port (send to)", "TDS-8 Bridge", 1024, 65535, 1, "", 8003);
   listenPort = prefs.getNumberSetting("Script listen port (Bridge sends to)", "TDS-8 Bridge", 1024, 65535, 1, "", 8001);
   bridgeHost.markInterested();
   sendPort.markInterested();
   listenPort.markInterested();

   var hostStr = String(bridgeHost.get());
   var outPort = Math.round(sendPort.getRaw());
   var inPort  = Math.round(listenPort.getRaw());

   var osc = host.getOscModule();

   // Answer the Bridge. It asks for names when you press Refresh, and on connect.
   var space = osc.createAddressSpace();
   space.registerMethod("/request-trackname", "*", "Send one track name", function (source, message) {
      var args = message.getArguments();
      if (args.size() < 1) return;
      sendName(Math.round(Number(args.get(0))));
   });
   space.registerMethod("/reannounce", "*", "Resend all track names", function (source, message) {
      sendAll();
   });
   space.registerMethod("/hello", "*", "Bridge handshake", function (source, message) {
      send("/hi");
   });
   space.registerDefaultMethod(function (source, message) { /* ignore anything else */ });

   try {
      osc.createUdpServer(inPort, space);
   } catch (e) {
      host.println("TDS-8: could not listen on UDP " + inPort + " (is Ableton's TDS-8 device open?). Names still send; Refresh will not.");
   }

   try {
      bridge = osc.connectToUdpServer(hostStr, outPort, null);
   } catch (e) {
      host.println("TDS-8: could not open OSC to " + hostStr + ":" + outPort + " " + e);
   }

   trackBank = host.createMainTrackBank(NUM_TRACKS, 0, 0);
   for (var i = 0; i < NUM_TRACKS; i++) {
      names[i] = "";
      watchTrack(i, trackBank.getItemAt(i));
   }

   host.scheduleTask(function () { sendAll(); }, 1000);
   host.scheduleTask(heartbeat, HEARTBEAT_MS);

   host.println("TDS-8: sending to " + hostStr + ":" + outPort + ", listening on " + inPort);
   host.showPopupNotification("TDS-8 connected");
}

function watchTrack(i, track) {
   track.name().markInterested();
   track.name().addValueObserver(function (value) {
      names[i] = value;
      sendName(i);
   });
   track.addIsSelectedInEditorObserver(function (isSelected) {
      if (isSelected) {
         selectedIndex = i;
         send("/activetrack", i);
      }
   });
}

function sendName(i) {
   if (i < 0 || i >= NUM_TRACKS) return;
   send("/trackname", i, names[i] || "");
}

function sendAll() {
   for (var i = 0; i < NUM_TRACKS; i++) sendName(i);
   if (selectedIndex >= 0) send("/activetrack", selectedIndex);
}

function heartbeat() {
   send("/hi");
   host.scheduleTask(heartbeat, HEARTBEAT_MS);
}

function send(address, a, b) {
   if (!bridge) return;
   try {
      // Explicit calls: Java varargs do not reliably accept Function.apply here.
      if (b !== undefined)      bridge.sendMessage(address, a, b);
      else if (a !== undefined) bridge.sendMessage(address, a);
      else                      bridge.sendMessage(address);
   } catch (e) {
      // Bridge not running yet. Nothing to do; the next rename or heartbeat retries.
   }
}

function flush() { }

function exit() {
   bridge = null;
}
