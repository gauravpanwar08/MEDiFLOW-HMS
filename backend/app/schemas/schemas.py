from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from app.models.models import UserRole, AppointmentStatus, AppointmentPriority, DoctorSpecialty, Gender


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


class HospitalCreate(BaseModel):
    name: str
    slug: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    subscription_plan: str = "basic"


class HospitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    subscription_plan: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    role: str


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    hospital_slug: str = "default"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.patient
    phone: Optional[str] = None
    hospital_slug: str = "default"

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    hospital_id: int
    last_login: Optional[datetime] = None
    created_at: datetime


class DoctorCreate(BaseModel):
    specialty: DoctorSpecialty
    license_number: str
    qualification: Optional[str] = None
    experience_years: int = 0
    consultation_fee: float = 0.0
    bio: Optional[str] = None


class DoctorUpdate(BaseModel):
    specialty: Optional[DoctorSpecialty] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    bio: Optional[str] = None
    is_available: Optional[bool] = None


class DoctorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    hospital_id: int
    specialty: DoctorSpecialty
    license_number: str
    qualification: Optional[str] = None
    experience_years: int
    consultation_fee: float
    bio: Optional[str] = None
    is_available: bool
    rating: float
    total_reviews: int
    user: UserOut


class DoctorAvailabilityCreate(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int = 30


class DoctorAvailabilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    doctor_id: int
    day_of_week: int
    start_time: str
    end_time: str
    slot_duration_minutes: int
    is_active: bool


class AvailableSlot(BaseModel):
    time: str
    available: bool


class PatientCreate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    current_medications: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None


class PatientUpdate(PatientCreate):
    pass


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    hospital_id: int
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    current_medications: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_number: Optional[str] = None
    user: UserOut


class AppointmentCreate(BaseModel):
    doctor_id: int
    appointment_date: date
    time_slot: str
    reason: Optional[str] = None
    symptoms: Optional[str] = None
    priority: AppointmentPriority = AppointmentPriority.routine

    @field_validator("appointment_date")
    @classmethod
    def not_past(cls, v):
        from datetime import date as d
        if v < d.today():
            raise ValueError("Appointment date cannot be in the past")
        return v


class AppointmentUpdate(BaseModel):
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    follow_up_date: Optional[date] = None
    cancelled_reason: Optional[str] = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    hospital_id: int
    patient_id: int
    doctor_id: int
    appointment_date: date
    time_slot: str
    duration_minutes: int
    status: AppointmentStatus
    priority: AppointmentPriority
    reason: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    follow_up_date: Optional[date] = None
    reminder_sent: bool
    cancelled_reason: Optional[str] = None
    created_at: datetime
    patient: Optional[PatientOut] = None
    doctor: Optional[DoctorOut] = None


class MedicalRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    patient_id: int
    appointment_id: Optional[int] = None
    file_name: str
    file_type: str
    file_size: int
    title: Optional[str] = None
    description: Optional[str] = None
    record_type: str
    is_confidential: bool
    created_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    ip_address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    user: Optional[UserOut] = None


class SymptomAnalysisRequest(BaseModel):
    symptoms: List[str]
    age: Optional[int] = None
    gender: Optional[str] = None
    medical_history: Optional[str] = None


class SymptomAnalysisResponse(BaseModel):
    suggested_conditions: List[dict]
    recommended_specialist: str
    urgency_level: str
    advice: str
    disclaimer: str


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str


class AnalyticsSummary(BaseModel):
    total_patients: int
    total_doctors: int
    total_appointments: int
    appointments_today: int
    appointments_this_week: int
    appointments_this_month: int
    pending_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    revenue_this_month: float


class DoctorWorkload(BaseModel):
    doctor_id: int
    doctor_name: str
    specialty: str
    total_appointments: int
    completed: int
    pending: int
    cancelled: int
    avg_rating: float
