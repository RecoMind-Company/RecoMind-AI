# import json
# from shared.config import get_llm
# from .answering_context_builder import create_crew_and_params

# # ======================================================
# # 1) إعداد بيانات الاختبار
# # ======================================================

# TEST_QUERY = "How many orders were made in 2014?"
# COMPANY_ID = "fb140d33-7e96-474d-a06d-ab3a6c65d1a9"
# TEAM_NAME = "Sales"

# print("\n============================================")
# print("🚀 Starting Full System Test")
# print("============================================\n")

# # ======================================================
# # 2) إنشاء الـ Crew + تحميل الـ LLM الصحيح
# # ======================================================

# print("🔧 Initializing LLM...")

# try:
#     llm = get_llm()
#     print("✔ LLM initialized successfully.")
# except Exception as e:
#     print("❌ FAILED: LLM initialization failed!")
#     print(e)
#     exit()

# print("\n🔧 Creating Crew...")

# crew, source_settings = create_crew_and_params(
#     user_query=TEST_QUERY,
#     company_id=COMPANY_ID,
#     team_name=TEAM_NAME
# )

# if crew is None:
#     print("❌ FAILED: Crew creation failed!")
#     exit()

# print("✔ Crew created successfully.")
# print("\n📦 Source DB Settings:")
# print(json.dumps(source_settings, indent=2))

# # ======================================================
# # 3) تشغيل الـ Crew Sequential
# # ======================================================

# print("\n============================================")
# print("▶ Running Crew...")
# print("============================================\n")

# try:
#     result = crew.kickoff()
# except Exception as e:
#     print("❌ ERROR while running the Crew!")
#     print(e)
#     exit()

# # ======================================================
# # 4) عرض النتيجة النهائية
# # ======================================================

# print("\n============================================")
# print("🎉 FINAL RESULT")
# print("============================================\n")
# print(result)
# print("\n============================================\n")


# test_local.py - تيست واحد بس + شغّال 100% مع Ollama

from answering_context_builder import create_crew_and_params
from shared.config import get_llm

# السؤال اللي عايزين نجربه
TEST_QUERY = "How many orders were made in 2014?"

print("جاري تهيئة الموديل المحلي (Ollama)...")
llm = get_llm()
print(f"الموديل شغال بنجاح: {llm.model}")
print("-" * 70)

print(f"السؤال: {TEST_QUERY}")
print("-" * 70)

# إنشاء الـ Crew
crew, source_settings = create_crew_and_params(
    user_query=TEST_QUERY,
    company_id="fb140d33-7e96-474d-a06d-ab3a6c65d1a9",
    team_name="Sales"
)

if not crew:
    print("فشل في إنشاء الـ Crew – تأكد من الداتابيز والاتصال")
    exit()

print("الـ Crew جاهز… بدء التنفيذ دلوقتي…\n")

try:
    result = crew.kickoff()
    print("\nالإجابة النهائية:")
    print("=" * 50)
    print(result)
    print("=" * 50)
except Exception as e:
    print("حصل خطأ أثناء التنفيذ:")
    print(e)
    import traceback
    traceback.print_exc()