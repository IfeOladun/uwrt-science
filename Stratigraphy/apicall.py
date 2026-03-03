import os, time
from google import genai
from google.genai.errors import ServerError
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key)

def ask_gemini(image_url, question):
    with open(image_url, "rb") as f:
        image_bytes = f.read()

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
        genai.types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg",
        ),
        question
        ]
    )

    return response.text

question = "Can you tell me the original depositional environment of the " \
            "strata in this image. The depositional environment must be one of these: Fluvial, " \
            "Alluvial, Lacustrine, Paludal, Aeolian, or Glacial. Note that there is only one " \
            "strata present in the photo. Give reasoning behind why the strata is " \
            "from the corresponding depositional environment. Don't respond in markdown. " \
            "Respond with Depositional Environment: and Reasoning: sections. It should be a " \
            "dict like this: {'Depositional Environment': '...', 'Reasoning': '...'}. " \
            "Don't add any extra spaces for any reason."
img_path = "./seperated_images"
number_of_images = 4

for index in range(number_of_images):
    try:
        response = ask_gemini(f"{img_path}/{index}.png", question)
        if response == None:
            print("No response from Gemini. Trying Again.")
            response = ask_gemini(img_path, question)
    except ServerError as e:
        print("Server Error. Trying Again.")
        time.sleep(30)
        response = ask_gemini(img_path, question)

    print(response)
