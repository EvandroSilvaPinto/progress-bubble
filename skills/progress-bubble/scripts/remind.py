"""UserPromptSubmit hook output: makes Progress Bubble run on every interaction."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
print('Progress Bubble: aplique a skill progress-bubble nesta interação (invoque /progress-bubble). '
      'Primeiro feche as bolinhas concluídas deste chat; depois, se a demanda levar mais de 30 segundos, '
      'abra o acompanhamento e mantenha-o atualizado até a entrega.')
