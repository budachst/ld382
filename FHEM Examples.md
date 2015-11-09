# How to integrate ld382a.py with FHEM

There are several ways to stitch the ld382a.py and FHEM together and the examples below are only intended as a staring point. The following examples will be lined out:

- request a direct set
- request a transition
- run an effect
- query the internal states of the saved values for RGBW and HSI

The examples below are meant to be placed inside the 99_myUtils.pm - or where else one is comfortable with.

## Request a direct set (RGBW or HSI) or a transition
Each of the above can be achieved by placing the following code inside the 99_myUtils.pm file:

```perl
sub transition($) {
  my ($cmdBlock) = @_;
  my ($socket,$client_socket);
  $socket = new IO::Socket::INET (
    PeerHost => '127.0.0.1',
    PeerPort => '5382',
    Proto => 'tcp',
  ) or die "ERROR in Socket Creation : $!\n";
  $socket->send($cmdBlock);
  $socket->close();
}
```
This sub can simply be called with the appropriate cmdBlock as the parameter like this:

`transition("s,0,100,0")` to set a HSI set on the device
`transition("r,0,0,0,0")` to set an RGBW set on the device
`transition("t,0,100,0,0,100,100,1")` to run a transition from HSI(A) to HSI(B) 
`transition("t,0,100,100,1")` to run a transition from the last saved internal values to HSI
