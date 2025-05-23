import dash
from dash import dcc
from dash import html
from dash import callback, Output, Input, State
from ollama_bot import OllamaBot
from config import ollama_config


# Инициализация приложения
app = dash.Dash(__name__)
ollama_bot = OllamaBot(ollama_config.binary_path)

# Определение макета приложения
app.layout = html.Div(children=[
	html.H1(children='Чат с самым умным помощником'),
	html.Label('Введите свой вопрос:'),
	html.Div([dcc.Input(id='input-question', type='text', value='prompt...')]),
	html.Button('Submit', id='submit-button'),
	html.Plaintext(id='my-output', children="")
])


@callback(
	Output(component_id='my-output', component_property='children'),
	State(component_id='input-question', component_property='value'),
	Input(component_id='submit-button', component_property='n_clicks'),
)
def update_output_div(input_value, n_clicks):
	if n_clicks == 0:
		return ''
	if input_value and input_value != 'prompt...':
		res = ollama_bot.ask(input_value)
		return res
	return 'Empty'


if __name__ == '__main__':
	app.run_server(debug=True)
