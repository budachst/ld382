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

- `transition("s,0,100,0")` to set a HSI set on the device
- `transition("r,0,0,0,0")` to set an RGBW set on the device
- `transition("t,0,100,0,0,100,100,1")` to run a transition from HSI to H'S'I' with duration 1
- `transition("t,0,100,100,2")` to run a transition from the last saved internal values to HSI with duration 2

## Request the current saved values for RGBW and HSI
To be able to reflect the current internal state of the values in a Wifilight device, one can query the server process for the current values of its internal RGBW and HSI variables. Again, this would be best suited as a sub in the 99_myUtils.pm:

```perl
sub getLD382aValues($) {
  my ($wifilightDevice) = @_;
  my ($socket,$client_socket);
  my $answer;

  $socket = new IO::Socket::INET (
    PeerHost => '127.0.0.1',
    PeerPort => '5382',
    Proto => 'tcp',
  ) or die "ERROR in Socket Creation : $!\n";
  $socket->send("g");
  $answer=<$socket>;
  $socket->close();
  # split $answer and set values in wifilight device
  my @array = split(',', $answer);
  # calculate RGB hex value from answer
  my $hex = sprintf("%02x",$array[0]).sprintf("%02x",$array[1]).sprintf("%02x",$array[2]);
  # set values of wifilight device
  fhem("setreading $wifilightDevice RGB $hex");
  fhem("setreading $wifilightDevice hue $array[4]");
  fhem("setreading $wifilightDevice saturation $array[5]");
  fhem("setreading $wifilightDevice brightness $array[6]");
}
```
This sub will be called with the name of the Wifilight device. It will query the server process and write the received values into the readings of the provided Wifilight device. It can be called like this:
- `getLD382aValues("<Name of Wifilight>")`
