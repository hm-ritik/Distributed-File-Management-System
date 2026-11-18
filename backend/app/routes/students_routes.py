from fastapi import APIRouter , Depends , Request
from app.core.dependencies import get_current_user , create_access_token , require_admin,get_db
from app.schemas.student_schema import Register , Login , ResponseRegister , Token
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.student_service import register_user as register_user_service
from app.services.student_service import login_user
from app.services.student_service import change_password
from app.schemas.student_schema import ChangePassword 
from app.models.students_model import Student
from app.schemas.student_schema import CurrentUser
from app.services.student_service import get_current_user_details
from app.middlewares.rate_limiter import limiter



router=APIRouter()

@router.post("/register" , response_model=ResponseRegister )
@limiter.limit("10/minute")
async def register_user(request:Request , post:Register , db:AsyncSession=Depends(get_db), user=Depends(require_admin)):
    return await register_user_service(post, db, user)


@router.post("/login" , response_model=Token)
@limiter.limit("10/minute")
async def login(request:Request,post:Login , db:AsyncSession=Depends(get_db)):
    return await login_user(post, db)


@router.put("/change-password")
@limiter.limit("5/minute")
async def update_user_password(request:Request ,post: ChangePassword,db: AsyncSession = Depends(get_db),current_user: Student = Depends(get_current_user)):
    return await change_password(post, db, current_user)

@router.get("/me", response_model=CurrentUser)
async def current_user(current_user: Student = Depends(get_current_user)):
    return await get_current_user_details(current_user)