from threading import Thread
import base64
import flask
import redis
import uuid
import time
import json
import sys
import io
import algorithm
import numpy

IMAGE_QUEUE  = "image_queue"
BATCH_SIZE   = 32
DTYPE        = numpy.float32
SERVER_SLEEP = 0.25
CLIENT_SLEEP = 0.25


# initialize our Flask application, Redis server, and Keras model
app = flask.Flask(__name__)
db = redis.StrictRedis(host="localhost", port=6379, db=0)

def base64_encode_image(a):
  # base64 encode the input NumPy array
  return base64.b64encode(a).decode("utf-8")
 
def base64_decode_image(a, dtype, shape):
  # if this is Python 3, we need the extra step of encoding the
  # serialized NumPy string as a byte object
  if sys.version_info.major == 3:
    a = bytes(a, encoding="utf-8")
 
  # convert the string to a NumPy array using the supplied data
  # type and target shape
  a = np.frombuffer(base64.decodestring(a), dtype=dtype)
  a = a.reshape(shape)
 
  # return the decoded image
  return a

def pre_process_file(I):
  # if sys.version_info.major == 3:
  #   I = bytes(I, encoding="utf-8")
  # I = base64.decodestring(I)
  I = io.BytesIO(base64.b64decode(I))
  # print(type(I))
  # print(I[:10])
  return I

def classify_process():
  while True:
    # get BATCH_SIZE no of requests
    queue = db.lrange(IMAGE_QUEUE, 0, BATCH_SIZE - 1)
    n = 0
    for q in queue:
      q = json.loads(q.decode("utf-8"))
      q['input_file'] = pre_process_file(q['input_file'])
      item_id = q["id"]
      
      # compute result for one request
      result = algorithm.compute(q)
      # put result in queue
      db.set(item_id,json.dumps(result))
      n = n+1
    # delete the processed requests
    db.ltrim(IMAGE_QUEUE, n,-1)
    # sleep for some time before polling again
    time.sleep(SERVER_SLEEP)

@app.route("/predict", methods=["POST"])
def predict():
  # initialize the data dictionary that will be returned from the  view
  data = {"success": False}
 
  # ensure an image was properly uploaded to our endpoint
  if flask.request.method == "POST":
    if flask.request.files.get("input_file"):
      # print(flask.request.files["input_file"])
      input_file = flask.request.files["input_file"].read()
      
      #image = numpy.frombuffer(io.BytesIO(image).getbuffer())
      #image = numpy.zeros((3,3))
      #image = prepare_image(image, (IMAGE_WIDTH, IMAGE_HEIGHT))
 
      # ensure our NumPy array is C-contiguous as well,
      # otherwise we won't be able to serialize it
      #image = image.copy(order="C")
 
      # generate an ID for the classification then add the
      # classification ID + image to the queue


      # input_file = io.BytesIO(input_file)

      #input_file = numpy.frombuffer(input_file.getbuffer(),dtype="u8")
      #print(input_file.shape)
      input_file = base64.b64encode(input_file).decode("utf-8")


      k = str(uuid.uuid4())
      #d = {"id": k, "input_file": base64_encode_image(input_file)}
      d = {"id": k, "input_file": input_file}

      db.rpush(IMAGE_QUEUE, json.dumps(d))
      # keep looping until our model server returns the output
      # predictions
      while True:
        # attempt to grab the output predictions
        output = db.get(k)
 
        # check to see if our model has classified the input
        # image
        if output is not None:
          # add the output predictions to our data
          # dictionary so we can return it to the client
          output = output.decode("utf-8")
          data["output"] = json.loads(output)
 
          # delete the result from the database and break
          # from the polling loop
          db.delete(k)
          break
 
        # sleep for a small amount to give the model a chance
        # to classify the input image
        time.sleep(CLIENT_SLEEP)
 
      # indicate that the request was a success
      data["success"] = True
 
  # return the data dictionary as a JSON response
  return flask.jsonify(data)

# if this is the main thread of execution first load the model and
# then start the server
if __name__ == "__main__":
  # load the function used to classify input images in a *separate*
  # thread than the one used for main classification
  print("* Starting model service...")
  t = Thread(target=classify_process, args=())
  t.daemon = True
  t.start()
 
  # start the web server
  print("* Starting web service...")
  app.run()
