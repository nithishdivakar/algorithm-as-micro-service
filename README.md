## Algorithm as micro service

This repository contains codes which can help run a simple algorithm as a micro service. The algorithm can be writen as a simple input to output transformation format and the supporting codes in this repo will help host it as a rest apii which can handle multiple requests at once. The results are returned as a json response.

### Assumptions

The algorithm always takes in a file and input and the output is a python dictionary which can be easily converted to json format.  This easily includes most machine learning algorithms.
