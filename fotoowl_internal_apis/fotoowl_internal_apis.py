import requests
import base64
import json
import os

fotoowl_internal_api_key = os.environ.get("FOTOOWL_INTERNAL_API_KEY")
fotoowl_ftp_user_verify_api = os.environ.get("FOTOOWL_FTP_USER_VERIFY_API")
fotoowl_process_ftp_image_api = os.environ.get("FOTOOWL_PROCESS_FTP_IMAGE_API")

class FotoowlInternalApis:
    @staticmethod
    def verify_user_given_credentials(username: str, password: str):
        try:
            url = fotoowl_ftp_user_verify_api
                
            headers = {
                'Authorization': f"Basic {fotoowl_internal_api_key}",
                'Content-Type': 'application/json'
            }
            param_dict = {'username': username, 'password': password}

            response = requests.request("GET", url, headers=headers, params=param_dict)
            print(response.text)
            data = response.json().get("data")
            event_id = data.get("event_id")
            event_creator_id = data.get("creator_user_id")
            #collection_id = data.get("collection_id")
            collection_id = -1
            return event_id, event_creator_id, collection_id
        
        except Exception as e:
            return None,None,None
    
    @staticmethod
    def send_image_info_to_fotoowl_for_processing(ftp_user_id: str, image_path: str, content):
        try:
            url = fotoowl_process_ftp_image_api
                
            headers = {
                'Authorization': f"Basic {fotoowl_internal_api_key}",
                'Content-Type': 'application/json'
            }
            encoded_content = base64.b64encode(content).decode("utf-8")
            body = {
                "ftp_user_id": ftp_user_id,
                "image_path": image_path,
                "content_encoded": encoded_content
            }

            response = requests.request("POST", url, headers=headers, data=json.dumps(body))
            print(response.text)
        
        except Exception as e:
            return None