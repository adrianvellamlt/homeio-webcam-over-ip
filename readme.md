# Webcam Over IP
This small program streams a webcam over the local IP 127.0.0.1 with the specified port. The port specification allows one machine to stream multiple webcams over the same IP.

To run, just invoke the application with two arguments. The webcam index (0 if just one webcam is connected) and the port over which it is going to be streamed. Defaults are webcam index 0 and port 8089.
```
Invoke:
python webcam-over-ip {webcam-id} {port}
Example:
python webcam-over-ip 1 8090
```
## Notes:
- The application was tested with 3 webcams simultaneously. At the moment the application does not have a graceful teardown due to a background thread that looks for clients.
- Up to 5 clients are permitted. More are possible but in my use case, this was not needed so I limited it to 5.