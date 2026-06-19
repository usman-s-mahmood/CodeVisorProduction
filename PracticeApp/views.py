from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
import json
import cohere
import traceback
from django.http import JsonResponse
from django.conf import settings
from decouple import config
import time
from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Max
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
import math
from django.utils import timezone



# Create your views here.

@login_required(login_url='/auth/login')
def problem_solve_view(request, slug):
    # Fetch the exact problem based on the URL slug
    problem = get_object_or_404(AlgorithmProblem, slug=slug)
    
    # Optional: Ensure only students/staff can access this
    if hasattr(request.user, 'profile') and getattr(request.user.profile, 'role', '') != 'student' and not request.user.is_staff:
        messages.warning(request, "Only students can access the practice arena.", extra_tags='error')
        return redirect('/auth/dashboard')

    context = {
        'problem': problem,
    }
    return render(request, 'PracticeApp/problem_ide.html', context)

@login_required
def submit_code_evaluation(request, slug):
    if request.method == 'POST':
        try:
            # Parse the incoming JSON payload from the frontend
            data = json.loads(request.body)
            user_code = data.get('code', '')
            problem = get_object_or_404(AlgorithmProblem, slug=slug)

            # Initialize Cohere Client
            co = cohere.Client(config('COHERE_API_KEY_FOR_EVAL_ENGINE'))

            # The Master Prompt
            prompt = f"""
            You are a ruthless but fair Python judge for an elite coding platform.
            Problem Title: {problem.title}
            Problem Description: {problem.problem_description}
            Reference Solution (Optimal): {problem.reference_solution}
            Key Concepts that MUST be used: {problem.key_concepts_to_check}

            User's Submitted Code:
            {user_code}

            Task: Evaluate the user's code strictly. Does it completely solve the problem, hit the required time/space complexities, and handle edge cases? 
            Respond ONLY in valid JSON format using the exact schema below. Do not use Markdown block ticks.
            {{
                "passed": true or false,
                "feedback": "2 to 3 sentences explaining precisely what they did right, or exactly why it failed."
            }}
            """

            # Trigger command-a-03-2025
            response = co.chat(
                model='command-a-03-2025',
                message=prompt,
                response_format={"type": "json_object"} # Forces Cohere to output safe JSON
            )

            # Clean the LLM text before parsing to prevent crash if it uses markdown
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            elif raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            # Extract and parse the LLM's JSON response
            result = json.loads(raw_text.strip())
            passed = result.get('passed', False)
            feedback = result.get('feedback', 'No feedback was generated.')

            # --- ANTI-FARMING VAULT ---
            # Check if they already solved this problem BEFORE we save this new attempt
            already_solved = ProblemSubmission.objects.filter(
                user=request.user, 
                problem=problem, 
                passed=True
            ).exists()

            # Save the attempt to the database for later analysis & badges
            ProblemSubmission.objects.create(
                user=request.user,
                problem=problem,
                submitted_code=user_code,
                passed=passed,
                llm_feedback=feedback
            )

            # --- ELO MATH & DB SAVE ---
            awarded_elo = 0
            if passed and not already_solved:
                awarded_elo = problem.elo_requirement
                current_elo = request.user.profile.elo_score or 0
                
                # Update the profile and SAVE to the database
                request.user.profile.elo_score = current_elo + awarded_elo
                request.user.profile.save()

            # Send result back to the IDE Terminal
            return JsonResponse({
                'passed': passed, 
                'feedback': feedback,
                'elo': awarded_elo # Returns 0 if failed OR already solved
            })

        except Exception as e:
            print("\n=== EVALUATION PIPELINE CRASHED ===")
            traceback.print_exc() 
            print("===================================\n")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
@require_POST
def generate_ai_problem(request):
    try:
        user = request.user
        
        # --- 1. DAILY LIMIT CHECK ---
        today = timezone.now().date()
        daily_generated_count = AlgorithmProblem.objects.filter(
            is_ai_generated=True, 
            generated_by=user,
            created_at__date=today
        ).count()
        
        if daily_generated_count >= 5:
            return JsonResponse({'error': 'Daily limit reached. You can only generate 5 AI problems per day.'}, status=403)

        # --- 2. ELIGIBILITY CHECK ---
        passed_submissions = ProblemSubmission.objects.filter(
            user=user, 
            passed=True
        ).select_related('problem').order_by('-created_at')
        
        distinct_solved_problems = []
        problem_ids_seen = set()
        
        for sub in passed_submissions:
            if sub.problem.id not in problem_ids_seen:
                problem_ids_seen.add(sub.problem.id)
                distinct_solved_problems.append({
                    "title": sub.problem.title,
                    "difficulty": sub.problem.difficulty_level,
                    "tags": sub.problem.topic_tags
                })
            if len(distinct_solved_problems) == 5:
                break

        if len(distinct_solved_problems) < 5:
            return JsonResponse({'error': f'Solve {5 - len(distinct_solved_problems)} more distinct problems to unlock the AI Arena.'}, status=403)

        # --- 3. CONTEXT GATHERING (Profile + Recent AI Problem) ---
        user_profile = user.profile
        profile_context = {
            "role": getattr(user_profile, 'role', 'student'),
            "skill_level": getattr(user_profile, 'skill_level', 'beginner'),
            "interests": getattr(user_profile, 'interests', []),
            "elo_score": getattr(user_profile, 'elo_score', 0)
        }

        # Fetch the most recent AI problem generated by this user (if any)
        last_ai_problem = AlgorithmProblem.objects.filter(
            is_ai_generated=True, 
            generated_by=user
        ).order_by('-created_at').first()

        recent_ai_context = ""
        if last_ai_problem:
            recent_ai_context = f"\nSTUDENT'S MOST RECENT AI-GENERATED PROBLEM:\nTitle: {last_ai_problem.title}\nTags: {last_ai_problem.topic_tags}\n(Do NOT generate a problem similar to this one.)\n"

        # --- 4. COHERE LLM EXECUTION ---
        co = cohere.Client(config('COHERE_API_KEY_FOR_PROBLEM_GENERATION'))
        
        prompt = f"""You are an elite coding instructor and algorithmic problem designer. 
        Generate a highly personalized, unique coding problem tailored to this student's exact skill level.

        STUDENT PROFILE:
        {json.dumps(profile_context, indent=2)}

        STUDENT'S 5 MOST RECENTLY SOLVED PROBLEMS:
        {json.dumps(distinct_solved_problems, indent=2)}
        {recent_ai_context}
        INSTRUCTIONS:
        1. Design a COMPLETELY ORIGINAL algorithmic problem. You are STRICTLY FORBIDDEN from generating standard textbook or cliché LeetCode problems (e.g., Two Sum, FizzBuzz, Fibonacci, Palindrome checks, Reverse String).
        2. Invent a unique, engaging storyline (e.g., sci-fi, cybersecurity, inventory management, fantasy RPG mechanics) to wrap the logic. Do NOT duplicate the recently solved problems.
        3. CRITICAL LIMITATION: The problem MUST be purely algorithmic (focusing on arrays, strings, math, data structures, or logic). It MUST be solvable using ONLY built-in Python types without requiring ANY `import` statements. You are STRICTLY FORBIDDEN from generating problems that require file I/O (`open()`), system operations (`os`, `sys`, `subprocess`), networking (`socket`), or dynamic execution (`eval`, `exec`). The student's IDE is a highly restricted sandbox that will instantly crash if these are used.
        4. Format the problem description using Markdown. Include constraints and 2-3 Examples.
        5. Provide an optimal Python reference solution using ONLY built-in Python features.
        6. Provide 3 progressive hints

        OUTPUT FORMAT:
        Respond ONLY with a valid JSON object matching this schema. Do not include markdown block formatting.
        {{
            "title": "String",
            "problem_description": "String (Markdown)",
            "difficulty_level": "String ('beginner', 'intermediate', or 'advanced')",
            "elo_requirement": Integer (Strictly between 200 and 600. Do NOT exceed 600),
            "topic_tags": ["Array", "String"],
            "starter_code": "String",
            "reference_solution": "String",
            "key_concepts_to_check": "String",
            "progressive_hints": ["Hint 1", "Hint 2", "Hint 3"]
        }}
        """

        response = co.chat(
            model='command-a-03-2025',
            message=prompt,
            response_format={"type": "json_object"}
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```json"): 
            raw_text = raw_text[7:]
        elif raw_text.startswith("```"): 
            raw_text = raw_text[3:]
        if raw_text.endswith("```"): 
            raw_text = raw_text[:-3]

        problem_data = json.loads(raw_text.strip())

        # --- ELO FAILSAFE ---
        # If the LLM still hallucinates a crazy number, we override it to a max of 400
        safe_elo = int(problem_data.get('elo_requirement', 400))
        if safe_elo > 800:
            safe_elo = 400

        # --- 5. DATABASE INJECTION ---
        max_id_dict = AlgorithmProblem.objects.aggregate(Max('problem_id'))
        next_id = (max_id_dict['problem_id__max'] or 0) + 1

        base_slug = slugify(problem_data.get('title', 'ai-generated-problem'))
        unique_slug = f"ai-{base_slug}-{user.id}-{int(time.time())}"

        new_problem = AlgorithmProblem.objects.create(
            problem_id=next_id,
            slug=unique_slug,
            title=problem_data.get('title', 'AI Generated Challenge'), 
            problem_description=problem_data.get('problem_description', ''),
            difficulty_level=problem_data.get('difficulty_level', 'intermediate').lower(),
            elo_requirement=safe_elo,  # Using our safety-checked Elo
            topic_tags=problem_data.get('topic_tags', []),
            starter_code=problem_data.get('starter_code', 'def solution():\n    pass'),
            reference_solution=problem_data.get('reference_solution', ''),
            key_concepts_to_check=problem_data.get('key_concepts_to_check', ''),
            progressive_hints=problem_data.get('progressive_hints', []),
            is_ai_generated=True,
            generated_by=user
        )

        return JsonResponse({
            'success': True,
            'message': 'AI Problem generated successfully!',
            'redirect_url': f'/practice/solve/{new_problem.slug}/'
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to generate problem. The AI Engine might be overloaded.'}, status=500)

from .models import AlgorithmProblem, ProblemSubmission, Duel

@login_required
@require_POST
def create_duel(request):
    challenger = request.user
    opponent_username = request.POST.get('opponent_username')

    # --- 1. BASIC VALIDATION ---
    if not opponent_username:
        messages.error(request, "Please enter a valid username.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    opponent = User.objects.filter(username=opponent_username).first()
    
    if not opponent:
        messages.error(request, f"User @{opponent_username} not found. Are you sure they exist?", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    if challenger == opponent:
        messages.error(request, "You cannot duel yourself!", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    # --- 2. ANTI-SPAM LOCK ---
    pending_count = Duel.objects.filter(challenger=challenger, status='pending').count()
    if pending_count >= 3:
        messages.error(request, "You already have 3 pending challenges. Wait for someone to accept before sending more!", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    try:
        # --- 3. GATHER DUAL CONTEXT ---
        c_elo = getattr(challenger.profile, 'elo_score', 400)
        c_skill = getattr(challenger.profile, 'skill_level', 'beginner')
        
        o_elo = getattr(opponent.profile, 'elo_score', 400)
        o_skill = getattr(opponent.profile, 'skill_level', 'beginner')

        # Get recently solved problem IDs to avoid duplicates
        c_solved = list(ProblemSubmission.objects.filter(user=challenger, passed=True).values_list('problem__title', flat=True)[:3])
        o_solved = list(ProblemSubmission.objects.filter(user=opponent, passed=True).values_list('problem__title', flat=True)[:3])
        
        avoid_list = list(set(c_solved + o_solved))

        # --- 4. THE HYBRID AI PROMPT ---
        co = cohere.Client(config('COHERE_API_KEY_FOR_DUEL'))
        
        prompt = f"""You are an elite coding instructor and algorithmic problem designer. 
        You are designing a competitive 1v1 coding duel between two players.

        MATCHUP CONTEXT:
        - Player A (Challenger): {c_skill} level, {c_elo} Elo.
        - Player B (Opponent): {o_skill} level, {o_elo} Elo.
        
        RECENTLY SOLVED CONCEPTS TO AVOID: {avoid_list}

        INSTRUCTIONS:
        1. Design a COMPLETELY ORIGINAL algorithmic problem. DO NOT generate standard LeetCode problems (e.g., Two Sum, Fibonacci).
        2. Give it a creative, competitive storyline theme (e.g., hacking a mainframe, space race, gladiator combat).
        3. DIFFICULTY BALANCING: If both players have similar skill levels, make the problem balanced. If one player is significantly higher, design an asymmetric problem: the core logic must be solvable by the lower-skill player, but hitting optimal O(n) time/space limits should challenge the higher-skill player.
        4. CRITICAL LIMITATION: The problem MUST be solvable using ONLY built-in Python types without ANY `import` statements (NO os, sys, math, collections).
        5. Provide constraints, 2-3 Examples, an optimal reference solution, and 3 progressive hints.

        OUTPUT FORMAT:
        Respond ONLY with a valid JSON object. No markdown blocks outside the JSON values.
        {{
            "title": "String (A creative, competitive title)",
            "problem_description": "String (Markdown)",
            "difficulty_level": "{c_skill}",
            "elo_requirement": {(c_elo + o_elo) // 2},
            "topic_tags": ["Array", "String"],
            "starter_code": "def solve(data):\\n    pass",
            "reference_solution": "String",
            "key_concepts_to_check": "String",
            "progressive_hints": ["Hint 1", "Hint 2", "Hint 3"]
        }}
        """

        response = co.chat(
            model='command-a-03-2025',
            message=prompt,
            response_format={"type": "json_object"}
        )

        # --- Clean AI Output (Bypassing the UI Markdown Bug) ---
        raw_text = response.text.strip()
        marker = "`" * 3
        if raw_text.startswith(marker + "json"): raw_text = raw_text[7:]
        elif raw_text.startswith(marker): raw_text = raw_text[3:]
        if raw_text.endswith(marker): raw_text = raw_text[:-3]

        problem_data = json.loads(raw_text.strip())

        # Failsafe Elo
        safe_elo = int(problem_data.get('elo_requirement', (c_elo + o_elo) // 2))
        if safe_elo > 1000: safe_elo = (c_elo + o_elo) // 2

        # --- 5. CREATE THE ARENA ---
        max_id_dict = AlgorithmProblem.objects.aggregate(Max('problem_id'))
        next_id = (max_id_dict['problem_id__max'] or 0) + 1
        unique_slug = f"duel-{slugify(problem_data.get('title', 'arena'))}-{int(time.time())}"

        # 5a. Save the Problem
        new_problem = AlgorithmProblem.objects.create(
            problem_id=next_id,
            slug=unique_slug,
            title=problem_data.get('title', 'AI Duel Arena'), 
            problem_description=problem_data.get('problem_description', ''),
            difficulty_level=problem_data.get('difficulty_level', c_skill),
            elo_requirement=safe_elo,
            topic_tags=problem_data.get('topic_tags', []),
            starter_code=problem_data.get('starter_code', 'def solution():\n    pass'),
            reference_solution=problem_data.get('reference_solution', ''),
            key_concepts_to_check=problem_data.get('key_concepts_to_check', ''),
            progressive_hints=problem_data.get('progressive_hints', []),
            is_ai_generated=True,
            generated_by=challenger
        )

        # 5b. Save the Duel state
        Duel.objects.create(
            challenger=challenger,
            opponent=opponent,
            problem=new_problem,
            status='pending'
        )

        messages.success(request, f"Challenge sent to @{opponent.username}! Waiting for them to accept.", extra_tags='success')
        return redirect('/auth/dashboard#ai-arena')

    except Exception as e:
        traceback.print_exc()
        messages.error(request, "Failed to generate the duel arena. The AI engine might be overloaded.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')
    
    

@login_required
@require_POST
def accept_duel(request, duel_id):
    # --- 1. FETCH THE DUEL ---
    # get_object_or_404 is a Django shortcut that automatically throws a 404 page 
    # if a user tries to accept a duel ID that doesn't exist in the database.
    duel = get_object_or_404(Duel, id=duel_id)

    # --- 2. SECURITY CHECKS ---
    # Only the designated opponent is allowed to accept the handshake!
    if request.user != duel.opponent:
        messages.error(request, "You are not authorized to accept this duel.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    # Make sure the duel hasn't already been accepted, graded, or cancelled
    if duel.status != 'pending':
        messages.error(request, f"This duel is already {duel.status}.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    # --- 3. THE HANDSHAKE ---
    # Flip the status so the Challenger knows the fight is on
    duel.status = 'active'
    
    # Start the 1-hour independent timer for the Opponent exactly right NOW
    duel.opponent_start_time = timezone.now()
    
    duel.save()

    messages.success(request, "Duel Accepted! Your 1-hour timer has started. Good luck.", extra_tags='success')
    
    # --- 4. DEPLOY TO THE BATTLEFIELD ---
    # Redirect them straight into the Arena (Priority 3 view)
    return redirect(f'/practice/duel/arena/{duel.id}/')

@login_required
def duel_arena_view(request, duel_id):
    # --- 1. FETCH THE DUEL ---
    duel = get_object_or_404(Duel, id=duel_id)

    # --- 2. THE BOUNCER (Security Checks) ---
    # Kick out anyone who isn't the Challenger or the Opponent
    if request.user not in [duel.challenger, duel.opponent]:
        messages.error(request, "You are not authorized to enter this arena.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    # If it's pending, the Challenger cannot enter yet. 
    # This prevents the Challenger from looking at the problem before the Opponent is ready!
    if duel.status == 'pending':
        messages.info(request, "The arena is locked. Waiting for the opponent to accept.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')
        
    # If it's grading or completed, the coding phase is over.
    if duel.status in ['grading', 'completed']:
        messages.info(request, "This duel has concluded. Awaiting final results.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    # --- 3. THE CLOCK MANAGER & INDEPENDENT TIMERS ---
    if request.user == duel.challenger:
        # The Challenger's clock only starts the VERY FIRST TIME they enter the active arena
        if not duel.challenger_start_time:
            duel.challenger_start_time = timezone.now()
            duel.save()
            
        start_time = duel.challenger_start_time
        has_submitted = bool(duel.challenger_code) # True if they already submitted code
    else:
        # The Opponent's clock started the moment they clicked 'Accept'
        start_time = duel.opponent_start_time
        has_submitted = bool(duel.opponent_code)

    # --- 4. LAZY EVALUATION (The 1-Hour Lock) ---
    time_limit_seconds = 3600  # 1 Hour
    elapsed_seconds = (timezone.now() - start_time).total_seconds()
    
    # Calculate exactly how many seconds are left (can't go below 0)
    remaining_seconds = math.floor(max(0, time_limit_seconds - elapsed_seconds))

    # If time is up, or they already submitted, kick them back to the lobby
    if remaining_seconds == 0 or has_submitted:
        messages.warning(request, "Your time in the arena has expired, or you have already submitted. Waiting for Opponent.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    # --- 5. SERVE THE BATTLEFIELD ---
    context = {
        'duel': duel,
        'problem': duel.problem,
        'remaining_seconds': remaining_seconds, 
        # Notice we are NOT sending the other player's data/status to the frontend. No cheating!
    }
    
    return render(request, 'PracticeApp/duel_ide.html', context)

@login_required
@require_POST
def submit_duel_code(request, duel_id):
    duel = get_object_or_404(Duel, id=duel_id)
    submitted_code = request.POST.get('code', '').strip()

    # --- 1. SECURITY CHECKS ---
    if request.user not in [duel.challenger, duel.opponent]:
        messages.error(request, "You are not authorized to submit code here.", extra_tags='error')
        return redirect('/auth/dashboard#ai-arena')

    if duel.status not in ['active', 'grading']:
        messages.error(request, f"Cannot submit. The duel is currently: {duel.status}", extra_tags='error')
        return redirect(f'/practice/duel/arena/{duel.id}/')

    # --- 2. RECORD SUBMISSION ---
    is_challenger = (request.user == duel.challenger)
    
    if is_challenger:
        if duel.challenger_code:
            messages.error(request, "You have already submitted your code!", extra_tags='error')
            return redirect(f'/practice/duel/arena/{duel.id}/')
        duel.challenger_code = submitted_code
        time_taken = (timezone.now() - duel.challenger_start_time).total_seconds()
    else:
        if duel.opponent_code:
            messages.error(request, "You have already submitted your code!", extra_tags='error')
            return redirect(f'/practice/duel/arena/{duel.id}/')
        duel.opponent_code = submitted_code
        time_taken = (timezone.now() - duel.opponent_start_time).total_seconds()

    duel.save()

    # --- 3. CHECK IF WE WAIT OR GRADE ---
    # If the other player hasn't submitted yet, we just wait.
    if not duel.challenger_code or not duel.opponent_code:
        messages.success(request, "Code locked in! Waiting for your opponent to finish...", extra_tags='success')
        return redirect(f'/practice/duel/arena/{duel.id}/')

    # --- 4. THE GRANDMASTER JUDGE (If both are submitted) ---
    duel.status = 'grading'
    duel.save()

    try:
        co = cohere.Client(config('COHERE_API_KEY_FOR_DUEL'))
        
        prompt = f"""You are the Grandmaster Judge for a 1v1 coding duel. 
        You must evaluate two pieces of Python code solving the following problem.

        PROBLEM TITLE: {duel.problem.title}
        PROBLEM DESCRIPTION: {duel.problem.problem_description}
        REFERENCE SOLUTION: {duel.problem.reference_solution}

        PLAYER A (Challenger) CODE:
        {duel.challenger_code}

        PLAYER B (Opponent) CODE:
        {duel.opponent_code}

        INSTRUCTIONS:
        1. Evaluate both codes for logic, syntax, and optimality (Time/Space complexity).
        2. If one code is completely broken/fails logic, and the other passes, the passing code wins.
        3. If both pass, the one with cleaner, more optimal logic wins.
        4. If it is a dead tie in logic, output "tie".
        
        OUTPUT FORMAT:
        Respond ONLY with a valid JSON object. No markdown blocks outside the JSON values.
        {{
            "winner": "challenger" or "opponent" or "tie",
            "reasoning": "A short, brutal 2-sentence explanation of why they won or lost."
        }}
        """

        response = co.chat(
            model='command-a-03-2025',
            message=prompt,
            response_format={"type": "json_object"}
        )

        # Clean AI Output to avoid markdown UI bugs
        raw_text = response.text.strip()
        marker = "`" * 3
        if raw_text.startswith(marker + "json"): raw_text = raw_text[7:]
        elif raw_text.startswith(marker): raw_text = raw_text[3:]
        if raw_text.endswith(marker): raw_text = raw_text[:-3]

        judge_data = json.loads(raw_text.strip())
        winner_decision = judge_data.get('winner', 'tie').lower()

        # --- 5. ELO WAGER & CROWNING THE VICTOR ---
        c_profile = duel.challenger.profile
        o_profile = duel.opponent.profile

        if winner_decision == 'challenger':
            duel.winner = duel.challenger
            c_profile.elo_score += 25
            o_profile.elo_score = max(0, o_profile.elo_score - 15)
        elif winner_decision == 'opponent':
            duel.winner = duel.opponent
            o_profile.elo_score += 25
            c_profile.elo_score = max(0, c_profile.elo_score - 15)
        else:
            # It's a tie, no Elo changes
            duel.winner = None

        # Save profiles and finalize duel
        c_profile.save()
        o_profile.save()
        
        duel.status = 'completed'
        duel.save()
        
        # We save the AI's reasoning temporarily in messages so they see it instantly
        messages.success(request, f"Match Complete! Judge says: {judge_data.get('reasoning')}", extra_tags='success')

    except Exception as e:
        traceback.print_exc()
        messages.error(request, "The AI Judge encountered an error while grading. Please contact an admin.", extra_tags='error')
        
        # Revert status so they aren't permanently stuck in 'grading'
        duel.status = 'active'
        duel.save()

    return redirect(f'/practice/duel/arena/{duel.id}/')

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import TechDomain

# SECURITY GATE: This ensures only users marked as Staff or Admin can access this view
@user_passes_test(lambda u: u.is_staff, login_url='/auth/login/')
def add_topic_view(request):
    if request.method == 'POST':
        # Extract fields directly from the POST request
        name_input = request.POST.get('name', '').strip().lower()
        display_name_input = request.POST.get('display_name', '').strip()

        # Validation Check: Ensure fields aren't blank
        if not name_input or not display_name_input:
            messages.error(request, "All fields are required.", extra_tags='error')
            return redirect('/practice/certifications/add-topic/')

        # Validation Check: Ensure the slug name is unique to prevent database integrity crashes
        if TechDomain.objects.filter(name=name_input).exists():
            messages.error(request, f"A topic with the system name '{name_input}' already exists.", extra_tags='error')
            return redirect('/practice/certifications/add-topic/')

        try:
            # Create the topic and bind it to the staff member who made it
            TechDomain.objects.create(
                name=name_input,
                display_name=display_name_input,
                created_by=request.user
            )
            messages.success(request, f"Successfully added topic: {display_name_input}", extra_tags='success')
            return redirect('/auth/dashboard')
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}", extra_tags='error')
            return redirect('/practice/certifications/add-topic/')

    # GET request processing
    return render(request, 'PracticeApp/add_topic.html')

# Initializing the Cohere Client with your master key setup
co = cohere.Client(config('COHERE_API_KEY'))

@login_required
def create_quiz_view(request, domain_id):
    domain = get_object_or_404(TechDomain, id=domain_id)
    user = request.user

    # 1. ENFORCE SECURITY RULE: One shot per topic maximum
    if CertificationQuizAttempt.objects.filter(student=user, domain=domain).exists():
        messages.error(request, f"You have already initiated or completed a certification attempt for {domain.display_name}. Multiple attempts are not allowed.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 2. PROFILE ALGORITHM LOOKUP: Extract names of the 5 most recently solved distinct problems
    # Tweak this import to mirror the exact location of your submission tracker model!
    
    recent_solved = ProblemSubmission.objects.filter(
        user=user, 
        passed=True
    ).select_related('problem').values_list('problem__title', flat=True).distinct()[:5]
    
    solved_list = list(recent_solved)
    # Fallback profiling string if it is a fresh user account with an empty solve state
    solved_context = ", ".join(solved_list) if solved_list else "Basic introductory software logic variables"

    # 3. BUILD THE STRICT JSON-FORCING SYSTEM PROMPT
    system_prompt = (
        "You are an elite technical certification systems engine. Generate a comprehensive technical quiz containing EXACTLY 20 multiple-choice questions (MCQs).\n"
        f"The primary focus topic is: {domain.display_name}.\n"
        f"Calibrate the complexity scaling based on the user's recently completed problem histories: [{solved_context}].\n\n"
        "CRITICAL DIRECTION: You MUST return the output as a raw, single, valid JSON array containing exactly 20 objects. "
        "Do not write conversational intro text, concluding notes, or wrap the data inside markdown code blocks (like ```json). "
        "Every item object in the array must adhere exactly to this structural dictionary template:\n"
        "{\n"
        '  "id": 1,\n'
        '  "question": "Insert highly targeted technical question text here",\n'
        '  "choices": ["Option Alpha", "Option Beta", "Option Gamma", "Option Delta"],\n'
        '  "correct_answer": "Option Alpha"\n'
        "}"
    )

    try:
        # 4. DISPATCH SYNCHRONOUS RUN VIA COMMAND-R-03-2025
        response = co.chat(
            model="command-a-03-2025",
            message=system_prompt,
            temperature=0.25 # Tight temperature ensures rigid formatting layout adherence
        )
        print(response)
        # Clean up the string string payload in case the model dropped code-block decorators anyway
        clean_payload = response.text.strip()
        if clean_payload.startswith("```json"):
            clean_payload = clean_payload[7:]
        if clean_payload.endswith("```"):
            clean_payload = clean_payload[:-3]
        clean_payload = clean_payload.strip()

        # Parse string stream into native Python structured lists
        quiz_json_data = json.loads(clean_payload)

        # 5. COMMIT ARCHITECTURE BLOCK: Save the frozen quiz questions state
        attempt = CertificationQuizAttempt.objects.create(
            student=user,
            domain=domain,
            generated_quiz_data=quiz_json_data,
            status='pending'
        )
        
        # Immediate RAW REDIRECT straight to the active examination panel template view
        return redirect(f'/practice/certifications/quiz/{attempt.id}/')

    except Exception as e:
        # Graceful fallback safety net error catcher if parsing breaks or timeouts hit
        messages.error(request, f"Failed to initialize your AI certification assessment: {str(e)}. Please retry.", extra_tags='error')
        return redirect('/auth/dashboard')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CertificationQuizAttempt

@login_required
def take_certification_quiz_view(request, attempt_id):
    # Fetch the specific attempt tied to the logged-in student
    attempt = get_object_or_404(CertificationQuizAttempt, id=attempt_id, student=request.user)

    # 1. SECURITY & CHEATING GATE: If they already have a score or a non-pending state, kick them out
    if attempt.status in ['verified', 'rejected'] or attempt.score_percentage > 0.0 or attempt.user_responses:
        messages.error(request, "Access Denied: You cannot re-enter an ongoing or completed examination session.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 2. TIME GATE CALCULATOR: Check if their 30 minutes are already up based on creation time
    # (In case they try to close the tab and return hours later to bypass the frontend timer)
    time_elapsed = timezone.now() - attempt.created_at
    time_remaining_seconds = (30 * 60) - time_elapsed.total_seconds()

    if time_remaining_seconds <= 0:
        messages.error(request, "Time Exceeded: The 30-minute testing window for this certification has closed.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 3. EXTRACTION: Pull the raw JSON list of questions generated by Cohere
    quiz_questions = attempt.generated_quiz_data

    context = {
        'attempt': attempt,
        'quiz_questions': quiz_questions,
        'time_remaining_seconds': int(time_remaining_seconds), # Pass down raw seconds for JavaScript countdown
    }
    return render(request, 'PracticeApp/take_quiz.html', context)





# for testing purposes only!
# from django.shortcuts import render
# from django.contrib.auth.decorators import login_required

# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render

# @login_required
# def test_certification_quiz_view(request):
#     # Dummy attempt-like object
#     class DummyDomain:
#         display_name = "Software Engineering Certification"

#     class DummyAttempt:
#         id = 999
#         domain = DummyDomain()
#         created_at = None

#     attempt = DummyAttempt()

#     # Programming-focused MCQs
#     quiz_questions = [
#         {
#             "id": 1,
#             "question": "Which keyword is used to define a function in Python?",
#             "choices": ["function", "def", "fun", "define"]
#         },
#         {
#             "id": 2,
#             "question": "What does HTTP stand for?",
#             "choices": [
#                 "HyperText Transfer Protocol",
#                 "High Transfer Text Protocol",
#                 "Hyper Transfer Text Process",
#                 "HyperText Transmission Program"
#             ]
#         },
#         {
#             "id": 3,
#             "question": "Which of the following is a Django ORM method?",
#             "choices": ["query()", "filter()", "select()", "fetch()"]
#         },
#         {
#             "id": 4,
#             "question": "What is the output of: len('Django')?",
#             "choices": ["5", "6", "7", "Error"]
#         },
#         {
#             "id": 5,
#             "question": "Which database is commonly used with Django in production?",
#             "choices": ["MongoDB", "SQLite", "PostgreSQL", "Redis only"]
#         },
#         {
#             "id": 6,
#             "question": "Which HTML tag is used to create a hyperlink?",
#             "choices": ["<link>", "<a>", "<href>", "<url>"]
#         },
#         {
#             "id": 7,
#             "question": "Which HTTP method is typically used to update data?",
#             "choices": ["GET", "POST", "PUT", "TRACE"]
#         },
#         {
#             "id": 8,
#             "question": "What does SQL stand for?",
#             "choices": [
#                 "Structured Query Language",
#                 "Simple Query Language",
#                 "Sequential Query Logic",
#                 "Standard Question Language"
#             ]
#         },
#         {
#             "id": 9,
#             "question": "In Python, which data structure is immutable?",
#             "choices": ["List", "Dictionary", "Set", "Tuple"]
#         },
#         {
#             "id": 10,
#             "question": "Which of the following is NOT a JavaScript framework?",
#             "choices": ["React", "Vue", "Django", "Angular"]
#         }
#     ]

#     context = {
#         "attempt": attempt,
#         "quiz_questions": quiz_questions,
#         "time_remaining_seconds": 30 * 60,  # full 30 minutes
#     }

#     return render(request, "PracticeApp/take_quiz.html", context)







import json
import cohere
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import CertificationQuizAttempt

# Initializing the Cohere client using your master system configuration
co = cohere.Client(config('COHERE_API_KEY'))

@login_required
@require_POST # Security enforcement: This view only allows incoming POST requests from the form
def evaluate_quiz_view(request, attempt_id):
    # Fetch the exact quiz attempt instance matching the logged-in student
    attempt = get_object_or_404(CertificationQuizAttempt, id=attempt_id, student=request.user)

    # 1. SECURITY & DUPLICATE SUBMISSION GUARD: If already processed or scored, halt execution
    if attempt.status in ['verified', 'rejected'] or attempt.score_percentage > 0.0 or attempt.user_responses:
        messages.error(request, "Security Exception: This examination session has already been closed or submitted for audit.", extra_tags='error')
        return redirect('/auth/dashboard')

    # 2. EXTRACT STORED QUESTION METRICS
    quiz_questions = attempt.generated_quiz_data # This is our original generated JSON list of 20 objects
    
    user_answers_dict = {}
    correct_count = 0
    total_questions = len(quiz_questions)
    missed_topics_summary = []

    # 3. NATIVE GRADING FACTORY LAYER
    for q in quiz_questions:
        question_id = str(q.get('id'))
        correct_answer = q.get('correct_answer')
        question_text = q.get('question')
        
        # Read what choice the user submitted via POST for this specific radio button group name
        submitted_answer = request.POST.get(f'question_{question_id}', '').strip()
        
        # Map out and cache their response sheet
        user_answers_dict[f'question_{question_id}'] = submitted_answer
        
        # Cross-reference answer sheets natively with zero external dependencies
        if submitted_answer == correct_answer:
            correct_count += 1
        else:
            # Document a contextual hint about the question topic for Cohere's performance evaluation query
            missed_topics_summary.append(question_text)

    # 4. MATH PERCENTAGE CALCULATION
    final_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0.0

    # 5. CONSTRUCT TARGETED COHERE PERFORMANCE NOTE GENERATION PROMPT
    # We combine the numerical evaluation scores into one single quick prompt to avoid latency overhead
    missed_context = " | ".join(missed_topics_summary[:4]) if missed_topics_summary else "None. Flawless execution."
    
    evaluation_prompt = (
        "You are an elite automated technical assessment auditor. Review the performance of a candidate who just completed a quiz.\n"
        f"Topic Focus Field: {attempt.domain.display_name}.\n"
        f"Final Numerical Score: {correct_count} out of {total_questions} questions correct ({final_percentage:.1f}%).\n"
        f"Sample of Questions Missed/Flawed: [{missed_context}].\n\n"
        "TASK: Write a precise, constructive, 2-sentence technical evaluation report summarizing the candidate's core competency level based on these metrics. "
        "Do not include greeting phrases, conversational text, introductory statements, or generic sign-offs. Get straight to the performance critique."
    )

    performance_report_note = "Evaluation completed. Pending system moderator sign-off review panels."

    try:
        # Firing a single light text summary request via Command-R
        response = co.chat(
            model="command-a-03-2025",
            message=evaluation_prompt,
            temperature=0.4
        )
        if response.text:
            performance_report_note = response.text.strip()
            
    except Exception:
        # Fail gracefully: If the secondary API note call hits a rare timeout exception, 
        # we log a clean system fallback message so the quiz state doesn't crash or roll back.
        performance_report_note = f"Automated grading finalized with an exact score index of {final_percentage:.1f}%. Cohere summary generation timed out."

    # 6. ATOMIC TRANSACTION PERSISTENCE: Lock down records into the database
    # We combine the data sheet, user response fields, and the performance note all into our attempt model instance
    attempt.user_responses = user_answers_dict
    attempt.score_percentage = round(final_percentage, 2)
    attempt.status = 'pending' # Enters the review queue for view 5 and 6
    
    # Store the performance report inside the database model record. 
    # Since your model doesn't have a separate dedicated field for this text summary, 
    # the cleanest approach is to safely nest it directly into our JSON data payload!
    attempt.generated_quiz_data = {
        'questions': quiz_questions,
        'ai_performance_note': performance_report_note
    }
    attempt.save()

    # 7. NOTIFY & ROUTE HOME
    messages.success(
        request, 
        f"Quiz successfully compiled! Your evaluation score sheet ({final_percentage:.1f}%) has been locked and securely forwarded to system staff for review.", 
        extra_tags='success'
    )
    return redirect('/auth/dashboard')

from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import CertificationQuizAttempt

# SAFETY ENFORCEMENT: Only system moderators/staff can see the pending verification lists
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import CertificationQuizAttempt

@user_passes_test(lambda u: u.is_staff, login_url='/auth/login/')
def staff_queue_view(request):
    # 1. FETCH RAW DATASETS
    pending_list = CertificationQuizAttempt.objects.filter(
        status='pending'
    ).select_related('student', 'domain').order_by('-created_at')

    history_list = CertificationQuizAttempt.objects.filter(
        status__in=['verified', 'rejected']
    ).select_related('student', 'domain', 'reviewed_by').order_by('-updated_at')

    # 2. EXTRACT DUAL PAGE PARAMETERS FROM THE REQUEST URL
    pending_page_num = request.GET.get('pending_page', 1)
    history_page_num = request.GET.get('history_page', 1)

    # 3. PAGINATE WORKLOAD QUEUE (10 items per page)
    pending_paginator = Paginator(pending_list, 10)
    try:
        pending_attempts = pending_paginator.page(pending_page_num)
    except PageNotAnInteger:
        pending_attempts = pending_paginator.page(1)
    except EmptyPage:
        pending_attempts = pending_paginator.page(pending_paginator.num_pages)

    # 4. PAGINATE AUDITED HISTORY (10 items per page - FULLY INJECTED!)
    history_paginator = Paginator(history_list, 10)
    try:
        audited_history = history_paginator.page(history_page_num)
    except PageNotAnInteger:
        audited_history = history_paginator.page(1)
    except EmptyPage:
        audited_history = history_paginator.page(history_paginator.num_pages)

    context = {
        'pending_attempts': pending_attempts,
        'audited_history': audited_history,
    }
    return render(request, 'PracticeApp/staff_review_queue.html', context)






from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import CertificationQuizAttempt



@user_passes_test(lambda u: u.is_staff, login_url='/auth/login/')
def staff_detail_review_view(request, attempt_id):
    # Fetch the exact quiz attempt instance matching the ID route parameter
    attempt = get_object_or_404(CertificationQuizAttempt, id=attempt_id)
    
    # 🌟 THE STATE PROTECTION VALVE: If already processed, lock out and redirect!
    if attempt.status in ['verified', 'rejected']:
        messages.warning(
            request, 
            f"Operation Invalid: Certification attempt for {attempt.student.username} has already been reviewed and finalized.", 
            extra_tags='warning'
        )
        return redirect('/practice/certifications/staff-queue/')

    # Unpack the nested JSON metadata payload we structured in View 4
    quiz_payload = attempt.generated_quiz_data if isinstance(attempt.generated_quiz_data, dict) else {}
    
    # Safe retrieval fallback variables
    quiz_questions = quiz_payload.get('questions', [])
    ai_note = quiz_payload.get('ai_performance_note', 'No automated summary report was logged for this run.')
    user_responses = attempt.user_responses if isinstance(attempt.user_responses, dict) else {}

    # PROCESS FORM APPROVAL OR REJECTION STRINGS VIA POST
    if request.method == 'POST':
        action_decision = request.POST.get('action_decision', '').strip().lower()
        
        if action_decision == 'approve':
            attempt.status = 'verified'
            messages.success(request, f"Certification successfully issued to {attempt.student.username}.", extra_tags='success')
        elif action_decision == 'reject':
            attempt.status = 'rejected'
            messages.error(request, f"Certification attempt for {attempt.student.username} has been marked as rejected.", extra_tags='error')
        else:
            messages.error(request, "Invalid structural operational parameters passed.", extra_tags='error')
            return redirect(f'/practice/certifications/staff-review/{attempt.id}/')

        # Log audit metadata details and commit state changes
        attempt.reviewed_by = request.user
        attempt.updated_at = timezone.now()
        attempt.save()
        
        # Route back to the master list table view 5 cleanly using raw path link
        return redirect('/practice/certifications/staff-queue/')

    # Build contextual map sheet to allow precise template matching side-by-side loops
    formatted_questions_list = []
    for q in quiz_questions:
        q_id = str(q.get('id'))
        formatted_questions_list.append({
            'id': q_id,
            'question_text': q.get('question'),
            'choices': q.get('choices', []),
            'correct_answer': q.get('correct_answer'),
            'student_answer': user_responses.get(f'question_{q_id}', 'No response given')
        })

    context = {
        'attempt': attempt,
        'ai_note': ai_note,
        'formatted_questions': formatted_questions_list
    }
    return render(request, 'PracticeApp/staff_detail_review.html', context)

import io
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.graphics.shapes import Drawing, Rect
from .models import CertificationQuizAttempt

@login_required
def download_certification_pdf_view(request, attempt_id):
    # 1. FETCH & INSTANT ACCESS SECURITY CHECK
    # By filtering on student=request.user, a student can NEVER guess a URL and download someone else's certificate!
    attempt = get_object_or_404(CertificationQuizAttempt, id=attempt_id, student=request.user, status='verified')

    # Create an in-memory byte buffer to hold the PDF data stream safely
    buffer = io.BytesIO()
    
    # Setup document configuration using professional landscape Letter size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    story = []
    styles = getSampleStyleSheet()

    # Define custom corporate typography styles
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=34,
        leading=42,
        textColor=HexColor('#0d6efd'), # CodeVisor Corporate Blue
        alignment=1 # Centered
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=18,
        leading=24,
        textColor=HexColor('#495057'),
        alignment=1
    )
    
    name_style = ParagraphStyle(
        'CertName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=HexColor('#212529'),
        alignment=1
    )
    
    meta_style = ParagraphStyle(
        'CertMeta',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=10,
        leading=14,
        textColor=HexColor('#6c757d'),
        alignment=1
    )

    # Decorative Border Canvas Component Setup
    # This draws a clean double frame on the background canvas page layout natively
    def draw_background_borders(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(HexColor('#0d6efd'))
        canvas.setLineWidth(4)
        canvas.rect(20, 20, 752, 572) # Outer Frame Boundary Ring
        canvas.setStrokeColor(HexColor('#198754')) # Success Emerald Accent Core
        canvas.setLineWidth(1)
        canvas.rect(26, 26, 740, 560) # Inner Ribbon Trace line
        canvas.restoreState()

    # 2. CONSTRUCT THE PORTFOLIO CANVAS STORY TILES
    story.append(Spacer(1, 40))
    story.append(Paragraph("CODEVISOR PROFESSIONAL CERTIFICATION", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("This foundational credential token is proudly presented to", subtitle_style))
    story.append(Spacer(1, 25))
    story.append(Paragraph(attempt.student.get_full_name() or attempt.student.username, name_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"for successfully passing the independent competency evaluation framework in", subtitle_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(f"<b>{attempt.domain.display_name}</b>", name_style))
    story.append(Spacer(1, 25))
    story.append(Paragraph(f"Achieved Examination Score Index: {attempt.score_percentage}%", subtitle_style))
    story.append(Spacer(1, 60))
    
    # Secure tracking footer data matrix lines mapping to verify logic module inputs
    issue_date = attempt.updated_at.strftime("%B %d, %Y") if attempt.updated_at else attempt.created_at.strftime("%B %d, %Y")
    verification_url = f"http://codevisor.com/practice/certifications/verify/CV-{attempt.id:04d}/"
    
    story.append(Paragraph(f"Date Issued: {issue_date}  |  Review Audit Signature ID: {attempt.reviewed_by.username if attempt.reviewed_by else 'SYSTEM'}", subtitle_style))
    story.append(Spacer(1, 35))
    story.append(Paragraph(f"SECURE VERIFICATION TOKEN SYSTEM ID: CV-{attempt.id:04d}", meta_style))
    # story.append(Paragraph(f"Verify authenticity live at: {verification_url}", meta_style))

    # Build document
    doc.build(story, onFirstPage=draw_background_borders)

    # 3. STREAM STREAM BACK TO USER FILE DOWNLOAD PROMPT
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CodeVisor_Certification_{attempt.domain.name}.pdf"'
    return response

import re
from django.shortcuts import render
from .models import CertificationQuizAttempt

def verify_certification_public_view(request):
    query_token = request.GET.get('token', '').strip()
    attempt = None
    searched = False
    error_message = None

    if query_token:
        searched = True
        # Extract the trailing numeric digits out of formats like "CV-0014" or raw "14" using basic regex expressions
        match = re.search(r'(?:CV-)?0*(\d+)', query_token, re.IGNORECASE)
        
        if match:
            extracted_id = match.group(1)
            try:
                # Query strictly for successfully verified tokens
                attempt = CertificationQuizAttempt.objects.select_related('student', 'domain', 'reviewed_by').get(
                    id=extracted_id,
                    status='verified'
                )
            except CertificationQuizAttempt.DoesNotExist:
                error_message = f"No verified system credential record was discovered matching token marker reference '{query_token}'."
        else:
            error_message = "Invalid operational token structural format signature. Please utilize the standard layout pattern (e.g., CV-0012)."

    context = {
        'attempt': attempt,
        'searched': searched,
        'query_token': query_token,
        'error_message': error_message,
        'verify': True
    }
    return render(request, 'PracticeApp/public_verify.html', context)


























