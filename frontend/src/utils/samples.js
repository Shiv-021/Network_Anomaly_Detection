// Raw NSL-KDD sample records used across the app

export const SAMPLES = {
  // Normal
  normal: { duration:0,protocoltype:'tcp',service:'http',flag:'SF',srcbytes:232,dstbytes:8153,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:1,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:5,srvcount:5,serrorrate:0.2,srvserrorrate:0.2,rerrorrate:0,srvrerrorrate:0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:30,dsthostsrvcount:255,dsthostsamesrvrate:1.0,dsthostdiffsrvrate:0,dsthostsamesrcportrate:0.03,dsthostsrvdiffhostrate:0.04,dsthostserrorrate:0.03,dsthostsrvserrorrate:0.01,dsthostrerrorrate:0,dsthostsrvrerrorrate:0.01 },
  // DoS
  neptune: { duration:0,protocoltype:'tcp',service:'private',flag:'S0',srcbytes:0,dstbytes:0,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:123,srvcount:6,serrorrate:1.0,srvserrorrate:1.0,rerrorrate:0,srvrerrorrate:0,samesrvrate:0.05,diffsrvrate:0.07,srvdiffhostrate:0,dsthostcount:255,dsthostsrvcount:26,dsthostsamesrvrate:0.10,dsthostdiffsrvrate:0.05,dsthostsamesrcportrate:0.0,dsthostsrvdiffhostrate:0.0,dsthostserrorrate:1.0,dsthostsrvserrorrate:1.0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0.0 },
  smurf: { duration:0,protocoltype:'icmp',service:'ecr_i',flag:'SF',srcbytes:1032,dstbytes:0,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:511,srvcount:511,serrorrate:0,srvserrorrate:0,rerrorrate:0,srvrerrorrate:0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:255,dsthostsrvcount:255,dsthostsamesrvrate:1.0,dsthostdiffsrvrate:0,dsthostsamesrcportrate:1.0,dsthostsrvdiffhostrate:0,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0 },
  teardrop: { duration:0,protocoltype:'udp',service:'private',flag:'SF',srcbytes:28,dstbytes:0,land:0,wrongfragment:3,urgent:0,hot:0,numfailedlogins:0,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:10,srvcount:10,serrorrate:0,srvserrorrate:0,rerrorrate:0,srvrerrorrate:0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:255,dsthostsrvcount:255,dsthostsamesrvrate:1.0,dsthostdiffsrvrate:0,dsthostsamesrcportrate:1.0,dsthostsrvdiffhostrate:0,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0 },
  // U2R
  buffer: { duration:0,protocoltype:'tcp',service:'telnet',flag:'SF',srcbytes:236,dstbytes:486,land:0,wrongfragment:0,urgent:0,hot:2,numfailedlogins:0,loggedin:1,numcompromised:235,rootshell:1,suattempted:0,numroot:235,numfilecreations:0,numshells:2,numaccessfiles:1,ishostlogin:0,isguestlogin:0,count:1,srvcount:1,serrorrate:0,srvserrorrate:0,rerrorrate:0,srvrerrorrate:0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:6,dsthostsrvcount:255,dsthostsamesrvrate:0.17,dsthostdiffsrvrate:0.03,dsthostsamesrcportrate:1.0,dsthostsrvdiffhostrate:0.02,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0 },
  // Probe
  ipsweep: { duration:0,protocoltype:'icmp',service:'ecr_i',flag:'SF',srcbytes:8,dstbytes:0,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:18,srvcount:1,serrorrate:0,srvserrorrate:0,rerrorrate:0,srvrerrorrate:0,samesrvrate:0.06,diffsrvrate:0.07,srvdiffhostrate:0,dsthostcount:255,dsthostsrvcount:3,dsthostsamesrvrate:0.01,dsthostdiffsrvrate:0.04,dsthostsamesrcportrate:1.0,dsthostsrvdiffhostrate:0,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0 },
  nmap: { duration:0,protocoltype:'tcp',service:'private',flag:'S0',srcbytes:0,dstbytes:0,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:3,srvcount:3,serrorrate:1.0,srvserrorrate:1.0,rerrorrate:0,srvrerrorrate:0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:3,dsthostsrvcount:3,dsthostsamesrvrate:1.0,dsthostdiffsrvrate:0,dsthostsamesrcportrate:0,dsthostsrvdiffhostrate:0,dsthostserrorrate:1.0,dsthostsrvserrorrate:1.0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0 },
  satan: { duration:0,protocoltype:'tcp',service:'private',flag:'REJ',srcbytes:0,dstbytes:0,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:4,srvcount:1,serrorrate:0,srvserrorrate:0,rerrorrate:1.0,srvrerrorrate:1.0,samesrvrate:0.25,diffsrvrate:1.0,srvdiffhostrate:0,dsthostcount:255,dsthostsrvcount:10,dsthostsamesrvrate:0.04,dsthostdiffsrvrate:0.06,dsthostsamesrcportrate:0,dsthostsrvdiffhostrate:0,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:1.0,dsthostsrvrerrorrate:1.0 },
  portscan: { duration:0,protocoltype:'tcp',service:'private',flag:'REJ',srcbytes:0,dstbytes:0,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:511,srvcount:511,serrorrate:0,srvserrorrate:0,rerrorrate:1.0,srvrerrorrate:1.0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:255,dsthostsrvcount:255,dsthostsamesrvrate:1.0,dsthostdiffsrvrate:0,dsthostsamesrcportrate:0,dsthostsrvdiffhostrate:0,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:1.0,dsthostsrvrerrorrate:1.0 },
  // R2L
  guesspasswd: { duration:0,protocoltype:'tcp',service:'telnet',flag:'SF',srcbytes:4162,dstbytes:3124,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:3,loggedin:0,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:5,srvcount:5,serrorrate:0,srvserrorrate:0,rerrorrate:0,srvrerrorrate:0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:5,dsthostsrvcount:5,dsthostsamesrvrate:1.0,dsthostdiffsrvrate:0,dsthostsamesrcportrate:0.2,dsthostsrvdiffhostrate:0,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0 },
  warezclient: { duration:0,protocoltype:'tcp',service:'ftp_data',flag:'SF',srcbytes:27345,dstbytes:0,land:0,wrongfragment:0,urgent:0,hot:0,numfailedlogins:0,loggedin:1,numcompromised:0,rootshell:0,suattempted:0,numroot:0,numfilecreations:0,numshells:0,numaccessfiles:0,ishostlogin:0,isguestlogin:0,count:1,srvcount:1,serrorrate:0,srvserrorrate:0,rerrorrate:0,srvrerrorrate:0,samesrvrate:1.0,diffsrvrate:0,srvdiffhostrate:0,dsthostcount:8,dsthostsrvcount:8,dsthostsamesrvrate:1.0,dsthostdiffsrvrate:0,dsthostsamesrcportrate:0.12,dsthostsrvdiffhostrate:0,dsthostserrorrate:0,dsthostsrvserrorrate:0,dsthostrerrorrate:0,dsthostsrvrerrorrate:0 },
}

// Weighted simulation pool — 30% normal, rest spread across attack types
export const SIM_POOL = [
  'normal', 'normal', 'normal',
  'neptune', 'neptune',
  'smurf', 'teardrop',
  'buffer',
  'ipsweep', 'nmap', 'satan', 'portscan',
  'guesspasswd', 'warezclient',
]

export const SAMPLE_BUTTONS = [
  { key: 'normal',      label: '✅ Normal HTTP',    group: 'Normal' },
  { key: 'neptune',     label: '🐋 Neptune DoS',    group: 'DoS' },
  { key: 'smurf',       label: '😈 Smurf DoS',      group: 'DoS' },
  { key: 'teardrop',    label: '💧 Teardrop DoS',   group: 'DoS' },
  { key: 'buffer',      label: '💥 Buffer Overflow', group: 'U2R' },
  { key: 'ipsweep',     label: '📭 IP Sweep',        group: 'Probe' },
  { key: 'nmap',        label: '📊 Nmap Probe',      group: 'Probe' },
  { key: 'satan',       label: '🤔 Satan Probe',     group: 'Probe' },
  { key: 'portscan',    label: '🔍 Port Scan',       group: 'Probe' },
  { key: 'guesspasswd', label: '🔒 Guess Passwd',    group: 'R2L' },
  { key: 'warezclient', label: '📦 Warezclient',     group: 'R2L' },
]
