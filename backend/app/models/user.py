from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from typing import Optional, Any
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any) -> Any:
        from pydantic_core import core_schema
        return core_schema.no_info_plain_validator_function(cls.validate)

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema: Any, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return {"type": "string"}

class UserBase(BaseModel):
    email: str = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="User display name")
    picture: Optional[str] = Field(None, description="User profile picture URL")
    is_active: bool = Field(True, description="Whether the user account is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

class UserCreate(UserBase):
    google_id: str = Field(..., description="Google user ID")
    access_token: str = Field(..., description="Google access token")
    refresh_token: Optional[str] = Field(None, description="Google refresh token")
    token_expires_at: datetime = Field(..., description="Token expiration timestamp")

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated user display name")
    picture: Optional[str] = Field(None, description="Updated user profile picture URL")
    is_active: Optional[bool] = Field(None, description="Whether the user account is active")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    access_token: Optional[str] = Field(None, description="Updated Google access token")
    refresh_token: Optional[str] = Field(None, description="Updated Google refresh token")
    token_expires_at: Optional[datetime] = Field(None, description="Updated token expiration timestamp")

class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    google_id: str = Field(..., description="Google user ID")
    access_token: str = Field(..., description="Google access token")
    refresh_token: Optional[str] = Field(None, description="Google refresh token")
    token_expires_at: datetime = Field(..., description="Token expiration timestamp")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
