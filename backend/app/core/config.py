from pydantic_settings import BaseSettings , SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL:str
    REDIS_URL: str = "redis://redis:6379/0"
    SECRET_KEY:str
   
    AWS_ACCESS_KEY_ID:str
    AWS_SECRET_ACCESS_KEY:str
    AWS_REGION:str
    S3_BUCKET_NAME:str


    ALGORITHM:str="HS256"
    ACCESS_TOKEN_TIME: int = 30

  
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings=Settings()