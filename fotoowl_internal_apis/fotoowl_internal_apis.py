import requests
import os

fotoowl_internal_api_key = os.environ.get("FOTOOWL_INTERNAL_API_KEY")
fotoowl_ftp_user_verify_api = os.environ.get("FOTOOWL_FTP_USER_VERIFY_API")
fotoowl_event_picture_process_api = os.environ.get("FOTOOWL_EVENT_PICTURE_PROCESS_API")

class FotoowlInternalApis:
    @staticmethod
    def verify_user_given_credentials(user_id: str, password: str):
        try:
            url = fotoowl_ftp_user_verify_api
                
            headers = {
                'Authorization': f"Basic {fotoowl_internal_api_key}",
                'Content-Type': 'application/json'
            }
            param_dict = {'user_id': user_id, 'password': password}

            response = requests.request("GET", url, headers=headers, params=param_dict)
            print(response.text)
            data = response.json().get("data")
            ftp_user_id = data.get("ftp_user_id")
            event_id = data.get("event_id")
            event_user_id = data.get("event_user_id")
            return ftp_user_id,event_id,event_user_id
        
        except Exception as e:
            return None
    
    @staticmethod
    def send_uploded_image_info_to_event_picture_process(event_id: int, image_name: str, mime_type: str,
                                                         b2_id: str, path: str, user_id: str, height: int, width: int):
        try:
            url = fotoowl_event_picture_process_api
                
            headers = {
                'Authorization': f"Basic {fotoowl_internal_api_key}",
                'Content-Type': 'application/json'
            }
            
            body = {
                "event_id": event_id,
                "image_name": image_name,
                "mime_type": mime_type,
                "b2_id": b2_id,
                "path": path,
                "user_id": user_id,
                "height": height,
                "width": width,
                "collection_ids": [-1]
            }

            response = requests.request("POST", url, headers=headers, json=body)
            print(response.text)
        
        except Exception as e:
            return None