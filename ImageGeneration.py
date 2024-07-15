import openai
import requests
from io import BytesIO
import base64
import deepl

def imageGeneration(contry, city, OPENAI_API_KEY, DEEPL_AUTH_KEY):
    # OpenAI API 키 설정
    openai.api_key = OPENAI_API_KEY
    
    # 영어로 번역
    translator = deepl.Translator(DEEPL_AUTH_KEY)
    text = f'{contry} {city}'
    result = str(translator.translate_text(text, target_lang='EN-US'))
    
    # 이미지 생성
    response = openai.Image.create(
	prompt=result,
	n=1,
	size='1024x1024'
 )
    image_url = response['data'][0]['url']
    response = requests.get(image_url)
    img = BytesIO(response.content)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    return img_base64