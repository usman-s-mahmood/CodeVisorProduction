import cohere
import json
import traceback # To see exactly where it breaks
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from decouple import config
from .models import ChatSession, ChatMessage
from .ph3_views_logic import is_coding_question
from .ph2_ai_logic.ph2_pinecone_helper import search_knowledge_base


# Initialize Cohere
try:
    co = cohere.Client(config('COHERE_API_KEY'))
except Exception as e:
    print(f"COHERE INIT ERROR: {e}")

SYSTEM_PREAMBLE = '''

You are CodeVisor AI Coach, a sophisticated hybrid of a high-tier Technical Architect and a versatile polymath, meticulously engineered by Usman Shahid. Your core identity is that of an elite coding mentor, designed to deconstruct complex Data Structures and Algorithms (DSA) and provide industry-standard, optimized solutions.

Your Operational Directives:

The Technical Specialist: When presented with coding challenges or DSA inquiries, you must provide exceptionally clear, high-performance logic. Reference the provided documentation as your "Source of Truth," but augment it with your deep architectural intuition to ensure the user receives a world-class educational experience.

The Professional Pivot (Non-Coding Queries): You are not a restricted bot; you possess an expansive, high-fidelity knowledge base covering history, science, pop culture, and beyond. However, you must maintain your professional branding. Every non-technical response MUST begin with this precise, elegant disclaimer:

"While my primary mission is serving as your CodeVisor AI Coach to sharpen your technical edge, I am equally equipped to assist with your general curiosity. Regarding your inquiry:"

Tone and Style: Your voice is authoritative yet encouraging—the kind of mentor found in a Silicon Valley lead's office. You are concise, technically accurate, and always aim to exceed the user's expectations by providing "Beast Mode" insights that go one step deeper than asked.

Whether you are explaining the nuances of 0/1 Knapsack DP or the historical impact of the Roman Empire, you represent the pinnacle of AI-driven mentorship under the CodeVisor banner.

'''

@login_required
def chat_home(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'NexusAIApp/chat.html', {'sessions': sessions})

@login_required

def chat_home(request):

    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'NexusAIApp/chat.html', {'sessions': sessions})


# Change your preamble to this:
# SYSTEM_PREAMBLE = (
#     "You are CodeVisor AI, a coding assistant. You have access to specialized documents, "
#     "but you MUST also use your own extensive internal knowledge to provide complete "
#     "and helpful answers, especially for general questions or complex coding tasks."
# )

@login_required
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_msg = data.get('message')
            session_id = data.get('session_id')

            # 1. Session Logic (Keep as is)
            if session_id and session_id != "null":
                session = get_object_or_404(ChatSession, id=session_id, user=request.user)
            else:
                title = (user_msg[:30] + '...') if len(user_msg) > 30 else user_msg
                session = ChatSession.objects.create(user=request.user, title=title)

            ChatMessage.objects.create(session=session, role='user', content=user_msg)

            # 2. RAG Routing
            retrieved_docs = []
            is_coding = is_coding_question(user_msg)
            
            if is_coding:
                retrieved_docs = search_knowledge_base(user_msg)

            # 3. Call Cohere command-a-03-2025
            # We use a dictionary to dynamically build the request
            cohere_kwargs = {
                "message": user_msg,
                "model": "command-a-03-2025",
                "preamble": SYSTEM_PREAMBLE,
                "temperature": 0.4, # Slightly higher temperature allows more "creative" internal knowledge use
            }

            # Only add documents if they exist, but also add a 'Nudge' to the message
            if retrieved_docs:
                cohere_kwargs["documents"] = retrieved_docs
                # This 'Nudge' tells the model NOT to ignore its own brain
                cohere_kwargs["message"] = f"Reference the provided snippets if relevant, but answer fully using your general knowledge: {user_msg}"

            response = co.chat(**cohere_kwargs)
            bot_response = response.text
            
            sources = [doc['title'] for doc in retrieved_docs]

            # 4. Save & Return
            ChatMessage.objects.create(session=session, role='bot', content=bot_response)

            return JsonResponse({
                "response": bot_response,
                "session_id": session.id,
                "title": session.title,
                "sources": sources
            })

        except Exception as e:
            print(traceback.format_exc()) 
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
'''
@login_required
def chat_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_msg = data.get('message')
            session_id = data.get('session_id')

            # Handle Session Logic
            if session_id and session_id != "null":
                session = get_object_or_404(ChatSession, id=session_id, user=request.user)
            else:
                title = (user_msg[:30] + '...') if len(user_msg) > 30 else user_msg
                session = ChatSession.objects.create(user=request.user, title=title)

            # Save User Message
            ChatMessage.objects.create(session=session, role='user', content=user_msg)

            # Call Cohere (Using 'command' for maximum compatibility)
            response = co.chat(
                message=user_msg,
                preamble=SYSTEM_PREAMBLE,
                model="command-a-03-2025", 
                temperature=0.3
            )
            
            bot_response = response.text

            # Save Bot Message
            ChatMessage.objects.create(session=session, role='bot', content=bot_response)

            return JsonResponse({
                "response": bot_response,
                "session_id": session.id,
                "title": session.title
            })

        except Exception as e:
            # THIS WILL PRINT THE ERROR IN YOUR TERMINAL
            print("--- CHAT API CRASH ---")
            print(traceback.format_exc()) 
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
'''
@login_required
def get_session_history(request, session_id):
    # Retrieve the session, ensuring it belongs to the logged-in user
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    # CRITICAL: We fetch ALL messages linked to this session ID
    messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
    
    history = []
    for msg in messages:
        history.append({
            'role': msg.role,
            'content': msg.content
        })
    
    return JsonResponse({
        'title': session.title,
        'history': history
    })
    
from django.db.models import Q

@login_required
def search_chats(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})

    # Tier 1: Match Session Titles
    sessions_by_title = ChatSession.objects.filter(
        user=request.user, 
        title__icontains=query
    )

    # Tier 2 & 3: Match Message Content (User or Bot)
    # We find messages that match, then get their unique parent sessions
    messages_matching = ChatMessage.objects.filter(
        session__user=request.user,
        content__icontains=query
    ).select_related('session')

    # Combine them into a unique set of sessions
    results = []
    seen_ids = set()

    # Add Title matches first (Highest Priority)
    for s in sessions_by_title:
        results.append({'id': s.id, 'title': s.title, 'type': 'Title Match'})
        seen_ids.add(s.id)

    # Add Content matches
    for m in messages_matching:
        if m.session.id not in seen_ids:
            match_type = "Question Match" if m.role == 'user' else "Answer Match"
            results.append({
                'id': m.session.id, 
                'title': m.session.title, 
                'type': match_type
            })
            seen_ids.add(m.session.id)

    return JsonResponse({'results': results})    

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ChatSession

@login_required
def career_coach_home_view(request):
    # Fetch all chat sessions created by this user, ordered by most recent first
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'sessions': sessions,
    }
    # Rendering our isolated professional career workspace template sheet
    return render(request, 'NexusAIApp/career_coach.html', context)

import json
import cohere
import traceback
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from decouple import config
from .models import ChatSession, ChatMessage

# Initialize your Cohere client connection token wrapper safely
try:
    co = cohere.Client(config('COHERE_API_KEY'))
except Exception as e:
    print(f"COHERE RECRUITMENT INIT ERROR: {e}")

@login_required
@require_POST
def career_coach_api_view(request):
    try:
        # Unpack incoming asymmetric payload data packet
        data = json.loads(request.body)
        user_msg = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not user_msg:
            return JsonResponse({"error": "Prompt content cannot be empty."}, status=400)

        # 1. LIVE SESSION THREAD FACTORY CONSTRAINTS
        if session_id and session_id != "null" and session_id != "":
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            # Generate a clean, responsive title line snippet out of the first prompt text
            title = (user_msg[:27] + '...') if len(user_msg) > 30 else user_msg
            session = ChatSession.objects.create(user=request.user, title=title)

        # Record User Input Question inside Message history log
        ChatMessage.objects.create(session=session, role='user', content=user_msg)

        # 🌟 2. STEALTH PLATFORM METRICS DATA COUPLING HARVESTER
        user = request.user
        profile = getattr(user, 'profile', None)
        
        # Aggregate complete distinct passed algorithm tasks counts from AuthApp
        from PracticeApp.models import ProblemSubmission 
        problems_solved_count = ProblemSubmission.objects.filter(user=user, passed=True).values('problem').distinct().count()
        
        # Aggregate complete approved professional credentials passed counts from PracticeApp
        from PracticeApp.models import CertificationQuizAttempt
        passed_certs = CertificationQuizAttempt.objects.filter(student=user, status='verified').select_related('domain')
        cert_list = [cert.domain.display_name for cert in passed_certs]
        cert_context = ", ".join(cert_list) if cert_list else "No certified platforms cleared yet"

        # Aggregate open recruiting applications active statuses from JobsApp
        from JobsApp.models import JobApplication 
        active_apps = JobApplication.objects.filter(applicant=user).select_related('job')
        job_list = [app.job.title for app in active_apps]
        job_context = ", ".join(job_list) if job_list else "No active job market applications processed yet"

        # 🌟 3. MAP DYNAMIC SYSTEMS DIRECTIVES SYSTEM PREAMBLE
        career_coach_preamble = (
            "You are CodeVisor Career Guidance AI Coach, an elite corporate engineering mentor, Lead Architect, and veteran tech recruiter.\n"
            "Your explicit operational mission is to provide high-fidelity, actionable technical career counseling, mock interview critiques, and custom preparation blueprints.\n"
            "You are evaluating the candidate's real-time platform metrics dynamically. Do not invent details; use this live payload summary as your absolute foundation:\n\n"
            f"- Target Candidate Account Name: {user.username}\n"
            f"- Current CodeVisor ELO Rating: {profile.elo_score if profile and profile.elo_score else '1000'}\n"
            f"- System Categorized Skill Tier: {profile.skill_level if profile and profile.skill_level else 'Beginner'}\n"
            f"- Verified Algorithmic Tasks Solved: {problems_solved_count}\n"
            f"- Validated Certifications Achieved: [{cert_context}]\n"
            f"- Corporate Job Postings Applied To: [{job_context}]\n\n"
            "CRITICAL CONVERSATIONAL PROTOCOLS:\n"
            "1. NEVER give vague career cliches. Frame all strategic steps directly around their actual ELO scores, solved metrics, and job targets.\n"
            "2. Tone is sharp, highly encouraging, authoritative, and deeply objective—like a Silicon Valley principal giving feedback.\n"
            "3. 🌟 TO-DO CHECKLIST RULES: Whenever you formulate specific action steps, homework, or practice tracks for the user, you MUST append a dedicated summary block at the absolute end of your response labeled exactly: '### Immediate Action Items'. Inside that block, list every homework task precisely using markdown bracket check lines like: '- [ ] Complete task description'. Do not put text below the checklist."
        )

        # GATHER RECENT SESSIONS MEMORY STREAM HISTORY (Last 6 messages)
        past_messages = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:6]
        chat_history = []
        for msg in reversed(past_messages):
            cohere_role = "USER" if msg.role == 'user' else "CHATBOT"
            chat_history.append({"role": cohere_role, "message": msg.content})

        # 🌟 4. RUN HIGH-COMPLIANCE CONTEXT ANALYSIS VIA COMMAND-A-03-2025
        response = co.chat(
            model="command-a-03-2025",
            message=user_msg,
            preamble=career_coach_preamble,
            chat_history=chat_history,
            temperature=0.35
        )
        
        bot_response = response.text

        # Record AI Assistant Response inside history log
        ChatMessage.objects.create(session=session, role='bot', content=bot_response)

        return JsonResponse({
            "response": bot_response,
            "session_id": session.id,
            "title": session.title
        })

    except Exception as e:
        print("--- SYSTEM PLATFORM CAREER ADVISOR CRASH LOG ---")
        print(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)










































