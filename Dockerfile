# كنجيبو نسخة خفيفة ديال بايثون
FROM python:3.10-slim

# كنحددو فين غيكون الكود وسط السيرفر
WORKDIR /app

# كنكوبيوا ملف المكتبات هو الأول باش نديرو ليه install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# كنكوبيوا كاع الملفات ديال المشروع
COPY . .

# كنحلوا البور اللي كيحتاج Hugging Face
EXPOSE 7860

# الأمر باش كيبدا السيرفر (تأكد من البور 7860)
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]