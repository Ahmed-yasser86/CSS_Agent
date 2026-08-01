import asyncio
import os
from Nodes.GPT_ResearcherNode.ResearchNode import make_research
from Chains.GPT_Researcher import DEFAULT_PROFILE_PROMPT
from StateGraph import GraphState

async def run_research_experiment():
    # Actual user query for Sheikh Mostafa Al-Adawy
    actual_user_query = (
        "ابحث بشكل معمق وشامل عن الشيخ مصطفى العدوي (المعروف أيضًا باسم مصطفى بن العدوي بن أحمد، أبو عبد الله)، "
        "الداعية والمحدث المصري السلفي المولود سنة 1374هـ/1954م في قرية منية سمنود بمحافظة الدقهلية، مصر، وموقعه الرسمي mostafaaladwy.com. "
        "لا تخلطه بأي شخص آخر يحمل نفس الاسم.\n\n"
        "اجمع معلومات دقيقة ومنظمة في المحاور التالية:\n\n"
        "1. السيرة الذاتية والتعليمية: النشأة، التعليم النظامي، دراسته الهندسة الميكانيكية، رحلته لليمن وتتلمذه على مقبل بن هادي الوادعي، أبرز مشايخه وتلاميذه.\n\n"
        "2. المسيرة الدعوية والعلمية: تخصصه في علم الحديث والسنة، أهم مؤلفاته وكتبه وأبحاثه العلمية، المناصب أو اللجان العلمية التي شارك فيها، آراؤه ومنهجه الفكري (تياره السلفي المستقل).\n\n"
        "3. الحضور الإعلامي والرقمي: قنواته على يوتيوب، حساباته الرسمية على فيسبوك وتويتر/إكس وتيليجرام، موقعه الرسمي، طبيعة المحتوى الذي ينشره، وتكرار النشاط.\n\n"
        "4. الأحداث والأخبار البارزة: قضايا اعتقاله (نوفمبر 2020 بخصوص دعوته لمقاطعة فرنسا، ونوفمبر 2025 بخصوص تصريحاته عن المتحف المصري الكبير)، وأي قضايا أو جدل آخر ارتبط باسمه، ومواقفه من الأحداث السياسية والاجتماعية في مصر.\n\n"
        "5. الجمهور والتأثير: حجم متابعيه على المنصات المختلفة إن أمكن تقديره، طبيعة جمهوره، تقييم تأثيره ومكانته بين الدعاة السلفيين في مصر مقارنة بأمثال محمد حسان ومحمد حسين يعقوب وأبو إسحاق الحويني.\n\n"
        "6. آخر الأخبار والتطورات: أي أخبار حديثة عنه خلال آخر 6 أشهر.\n\n"
        "قدم التقرير بالعربية، مع ذكر المصادر بوضوح لكل معلومة."
    )

    # Prepare state with only the query to rely on defaults
    state: GraphState = {
        "user_initial_query": actual_user_query,
        "chain_input": {
            "query": actual_user_query,
        },
        "profile_candidates": [],
        "research_iteration": 0,
    }

    print("⏳ Running live research call, please wait...")
    
    # Execute the actual function (connects to live services and model)
    result = await make_research(state)

    # Validate that data is returned from the live call
    assert "profile_candidates" in result
    assert len(result["profile_candidates"]) == 1

    candidate = result["profile_candidates"][0]
    
    # Verify that the report and fields were successfully fetched and are not empty
    assert candidate["full_report"] and isinstance(candidate["full_report"], str)
    assert candidate["conclusion"] and isinstance(candidate["conclusion"], str)
    assert isinstance(candidate["costs"], (int, float)) and candidate["costs"] >= 0
    assert candidate["summary"] == ""  
    assert isinstance(candidate["sub_topics"], list)
    assert isinstance(candidate["sources"], list)

    # Verify iteration counter increment
    assert result["research_iteration"] == 1

    # ---- Save each field from the candidate results into separate Markdown files under "نتايج الاختبار" ----
    output_dir = "نتايج الاختبار"
    os.makedirs(output_dir, exist_ok=True)

    for field_name, field_value in candidate.items():
        file_path = os.path.join(output_dir, f"{field_name}.md")
        
        # Format the content appropriately depending on its data type
        if isinstance(field_value, list):
            content = "\n".join([str(item) for item in field_value])
        else:
            content = str(field_value)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Field: {field_name}\n\n{content}")

    print(f"✅ All fields successfully saved to directory: {output_dir}")

if __name__ == "__main__":
    asyncio.run(run_research_experiment())