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
sub getLD382aValuesNew($;$) {
  my ($wifilightDevice,$sleepTime)=@_;
  my ($socket,$client_socket);
  my $answer;
  my $cmdBlock = "g,$sleepTime";
  
  $socket = new IO::Socket::INET (
    PeerHost => '127.0.0.1',
    PeerPort => '5382',
    Proto => 'tcp',
  ) or die "ERROR in Socket Creation : $!\n";
  $socket->send("$cmdBlock");
  $answer=<$socket>;
  $socket->close();
  # split $answer and set values in wifilight device
  my @array = split(',', $answer);
  # calculate RGB hex value from answer
  my $rgb = sprintf("%02x",$array[0]).sprintf("%02x",$array[1]).sprintf("%02x",$array[2]);
  my $wht = sprintf("%02x",$array[3]);
  if ($rgb eq "000000" && $wht ne "00") {
    $rgb = "$wht$wht$wht";
  }
  if ($rgb ne "000000") {
    # set values of wifilight device
    fhem("setreading $wifilightDevice RGB $rgb");
    fhem("setreading $wifilightDevice hue $array[4]");
    fhem("setreading $wifilightDevice saturation $array[5]");
    fhem("setreading $wifilightDevice brightness $array[6]");
    fhem("setreading $wifilightDevice state on");
    fhem("setstate $wifilightDevice on");
  } else {
    fhem("setreading $wifilightDevice RGB $rgb");
    fhem("setreading $wifilightDevice state off");
    fhem("setstate $wifilightDevice off");
  }
}

```
This sub will be called with the name of the Wifilight device and or an additonal sleepTime of up to 10 seconds. It will query the server process and write the received values into the readings of the provided Wifilight device. It can be called like this:
- `getLD382aValues("<Name of Wifilight>"[,sleeptime])`

## Run and stop a built-in effect
Effects are more complex transitions, which are computed and performed on demand and are of a cyclic nature (well, most often, anyway). The fireplace simulation is a good example. It performs random, and very brief transitions over a quite narrow range of colors, saturations and intensities. Also, each effect has a duration, which marks the time in seconds this effect should be run. For a better experience the duration should be kept rather small, to ensure that further requests are served in a timely manner. To be able to to run the fireplace simulation actually longer than, say 1 second, we make use of FHEM's InternalTimer command, which will call itself again after the duration specified in the command block. This sub would take care of this:

```perl
sub dreamyFire(@) {
  my @params=@_;
  foreach (@params) {
    my $duration = $_;
 
    my $cmdBlock = "e,fire,$duration";
    my ($socket,$client_socket);
    $socket = new IO::Socket::INET (
      PeerHost => '127.0.0.1',
      PeerPort => '5382',
      Proto => 'tcp',
    ) or die "ERROR in Socket Creation : $!\n";
    $socket->send($cmdBlock);
    $socket->close();
    InternalTimer(gettimeofday()+$duration,'dreamyFire',$duration, 0);
  }
}
```
You would call this sub simply like this:
- `dreamyFire(2);` run the fire effect for two seconds

Now, you surely will want to stop this effect eventually and this little sub will take care of this:

```perl
sub stopDreamyFire(@) {
  my @params=@_;
  foreach (@params) {
    my $duration = $_;
    RemoveInternalTimer($duration);
  }
}
```
Note, that you will need to identify the currently running effect loop, by the duration - 2 in this case - and that you can stop the loop by calling the sub like this:
- `stopDreamyFire(2);` stops the running InternalTimer command with the "identifier" 2. There is some documentation about the InternalTimer command on the FHEM forums.
