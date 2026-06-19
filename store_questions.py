import os
import django
import json

# 1. Initialize the Django environment BEFORE importing models
# Replace 'CodeVisorProject' with the exact name of the folder containing your settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CodeVisorProject.settings')
django.setup()

# 2. Use an absolute import now that Django is awake
from PracticeApp.models import AlgorithmProblem

# 3. Adjust paths if your question_bank folder is in the root directory alongside manage.py
# If question_bank is in the same folder as this script, remove the '../'
files_to_load = [
    'question_bank/beginner.json', 
    'question_bank/intermediate.json', 
    'question_bank/advanced.json'
]

for filename in files_to_load:
    print(f"Processing {filename}...")
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
        for item in data:
            # Create or update the problem in the database
            AlgorithmProblem.objects.update_or_create(
                problem_id=item['problem_id'],
                defaults={
                    'title': item['title'],
                    'slug': item['slug'],
                    'difficulty_level': item['difficulty_level'],
                    'elo_requirement': item['elo_requirement'],
                    'topic_tags': item['topic_tags'],
                    'problem_description': item['problem_description'],
                    'starter_code': item['starter_code'],
                    'reference_solution': item['reference_solution'],
                    'key_concepts_to_check': item['key_concepts_to_check'],
                    'progressive_hints': item['progressive_hints']
                }
            )
            
print("All batches successfully imported into the CodeVisor database!")