import os
from obs import ObsClient, HeadPermission
from dotenv import load_dotenv
import traceback
from datetime import datetime

# Cargar variables de entorno desde .env
load_dotenv()

class HuaweiOBSUploader:
    def __init__(self):
        self.ak = os.getenv("HUAWEI_ACCESS_KEY")
        self.sk = os.getenv("HUAWEI_ACCESS_SECRET_KEY")
        self.server = os.getenv("HUAWEI_OBS_ENDPOINT")
        self.bucket_name = os.getenv("HUAWEI_BUCKET_NAME")
        
        if not all([self.ak, self.sk, self.server, self.bucket_name]):
            raise ValueError("Las credenciales de Huawei OBS no están configuradas correctamente.")

        self.obs_client = ObsClient(
            access_key_id=self.ak,
            secret_access_key=self.sk,
            server=self.server
        )
        
    def upload_image(self, local_file_path, original_filename=None):
        try:
            # Obtener el nombre del archivo y extensión
            if original_filename:
                _, ext = os.path.splitext(original_filename)
            else:
                _, ext = os.path.splitext(local_file_path)
            
            if not ext:
                ext = '.png'
                
            # Generar nombre único con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            object_key = f"scan_{timestamp}{ext}"
            
            # Subir archivo
            resp = self.obs_client.putFile(
                bucketName=self.bucket_name,
                objectKey=object_key,
                file_path=local_file_path
            )
            
            if resp.status < 300:
                # Establecer permisos públicos
                self.obs_client.setObjectAcl(
                    self.bucket_name,
                    object_key,
                    aclControl=HeadPermission.PUBLIC_READ_WRITE
                )
                
                # Generar URL pública
                endpoint = self.server.replace("https://", "").replace("http://", "")
                public_url = f"https://{self.bucket_name}.{endpoint}/{object_key}"
                
                return public_url
            else:
                print(f"Error al subir imagen: {resp.errorMessage}")
                return None
                
        except Exception as e:
            print(f"Error en upload_image: {str(e)}")
            traceback.print_exc()
            return None
            
    def list_images(self):
        try:
            images = []
            resp = self.obs_client.listObjects(self.bucket_name)
            
            if resp.status < 300:
                endpoint = self.server.replace("https://", "").replace("http://", "")
                
                for content in resp.body.contents:
                    if any(content.key.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        public_url = f"https://{self.bucket_name}.{endpoint}/{content.key}"
                        name = os.path.splitext(content.key)[0]
                        images.append({
                            'url': public_url,
                            'name': name,
                            'last_modified': content.lastModified
                        })
                
                return sorted(images, key=lambda x: x['last_modified'], reverse=True)
            else:
                print(f"Error al listar objetos: {resp.errorMessage}")
                return []
                
        except Exception as e:
            print(f"Error en list_images: {str(e)}")
            traceback.print_exc()
            return []
            
    def __del__(self):
        if hasattr(self, 'obs_client'):
            self.obs_client.close()