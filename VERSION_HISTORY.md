# VERSION HISTORY

##V. 0.1 - initial version
- implemented HSI color space

## V. 0.2
- implemented threaded server socket
- implemented time-based transisions
- implemented color correction based on intensity of LED colors

## V. 0.2.1
- implemented select-based non-blocking socket for reading
- implemented transition ringbuffer

## V. 0.2.2
- added fire effect

## V. 0.2.3
- added direct set for RGBW

## V. 0.2.4
- added saving of latest RGBW and HSI values for reuse

## V. 0.2.5
- added query for current saved RGBW and HSI values
- fixed possible DIV/0 if transition has 0 duration