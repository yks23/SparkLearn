## Avoiding collisions (more)

idea: sender "reserves" channel use for data frames using small reservation packets

■ sender first transmits small request-to-send (RTS) packet to BS using CSMA

*  RTSs may still collide with each other (but they're short)
* ■ BS broadcasts clear-to-send CTS in response to RTS
* ■ CTS heard by all nodes
*  sender transmits data frame
*  other stations defer transmissions



