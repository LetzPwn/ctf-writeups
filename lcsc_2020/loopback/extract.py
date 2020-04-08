import dpkt

#open the pcap file
pcap_content = open("./loopback.pcap", "rb")
#open the ouput file
out = open("flag.png", "wb")
#read in the file as series of packets
pcap = dpkt.pcap.Reader(pcap_content)
#set count variable to only get every second packet
count = 0
for cap in pcap:
	if count % 2 == 0:
		#write out the relevant byte of every second ICMP packet
		out.write(cap[1][70])
	count +=1
