import boto3
import os

class BotoB2:
    """session = aioboto3.Session(aws_access_key_id=os.environ["B2_BOTO_ACCESS_KEY_ID"],
                               aws_secret_access_key=os.environ["B2_BOTO_ACCESS_KEY"])"""
    
    s3_client_sync = boto3.client('s3',
                                  endpoint_url=os.environ["B2_BOTO_ENDPOINT_URL"],
                                  aws_access_key_id=os.environ["B2_BOTO_ACCESS_KEY_ID"],
                                  aws_secret_access_key=os.environ["B2_BOTO_ACCESS_KEY"]
                             )

    @staticmethod
    def upload_file(content, file_name, content_type):
        try:
            response = BotoB2.s3_client_sync.put_object(
                Body=content, Bucket=os.environ["B2_BUCKET_NAME"], Key=file_name, ContentType=content_type)
            error_msg = None
            if response is None:
                error_msg = f'null response from upload content_type: {content_type}, file_name: {file_name}'
            else:
                response_meta_data = response.get('ResponseMetadata')
                if response_meta_data is None:
                    error_msg = f'null response from upload content_type: {content_type}, file_name: {file_name} response: {response}'
                else:
                    status_code = response_meta_data.get('HTTPStatusCode')
                    if status_code != 200:
                        error_msg = f'null response from upload content_type: {content_type}, file_name: {file_name} response: {response}'
            if error_msg:
                return None
            return response['ResponseMetadata']['HTTPHeaders']['x-amz-version-id']
            
        except Exception as e:
            error_msg = f'error upload_file content_type: {content_type} path:{file_name}, error: {e.__str__()}'
    
    @staticmethod
    def upload_ftp_uploaded_image_to_event_bucket(content, content_type: str, file_name: str, event_id: int, event_user_id: str):
        file_path_raw = f"events/{event_id}/{event_user_id}/raw/{file_name}"
        raw_id = BotoB2.upload_file(content=content, file_name=file_path_raw, content_type=content_type)
        return raw_id, file_path_raw