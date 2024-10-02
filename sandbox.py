# import gspread
# from google.oauth2.service_account import Credentials
# import pandas as pd

# # Path to the service account key file
# SERVICE_ACCOUNT_FILE = './data-extraction-tool-433301-f79d60b07ff8.json'

# # Scopes for the service account
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# # Load the service account credentials
# credentials = Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE,
#     scopes=SCOPES
# )

# # Authorize the client
# gc = gspread.authorize(credentials)

# # Document ID extracted from the link
# DOCUMENT_ID = '154VvsJcn7ZKE7mqPEIP1T-JIJbEzw4IyEExPZesa2Gc'

# def update_existing_data(df, condition_col, condition_val, new_col, new_val):
#     """
#     Updates existing data in a Google Sheet based on a condition.

#     Parameters:
#     - df: Pandas DataFrame containing the data to be written to the Google Sheet.
#     - condition_col: The column name in the DataFrame to check against the condition.
#     - condition_val: The value to match in the condition column.
#     - new_col: The column name in the DataFrame containing the new values to update.
#     - new_val: The new value to update the matched rows with.
#     """
#     # Get column index for condition_col and new_col
#     condition_col_idx = df.columns.get_loc(condition_col) + 1  # Google Sheets indices start at 1
#     new_col_idx = df.columns.get_loc(new_col) + 1

#     # Iterate over each row in the DataFrame
#     for index, row in df.iterrows():
#         # Check if the condition matches
#         if str(row[condition_col]) == str(condition_val):
#             # Update the corresponding cell in the Google Sheet
#             try:
#                 worksheet.update_cell(index + 2, new_col_idx, new_val)
#                 print(f"Updated cell at row {index + 2}, column {new_col_idx} with value {new_val}.")
#             except Exception as e:
#                 print(f"Failed to update cell at row {index + 2}, column {new_col_idx}. Error: {e}")

# # Open the Google Spreadsheet by ID
# spreadsheet = gc.open_by_key(DOCUMENT_ID)

# # Assuming SHEET_ID is the index of the worksheet you want to access
# # For example, if you want to access the first worksheet, SHEET_ID would be 0
# SHEET_ID = 0  # Change this to the index of the worksheet you want to access

# # Select the worksheet by index
# worksheet = spreadsheet.get_worksheet(SHEET_ID)

# # Read all records from the worksheet
# list_of_rows = worksheet.get_all_records()

# # Convert the list of rows to a DataFrame
# df = pd.DataFrame(list_of_rows)

# # Display the first few rows of the DataFrame
# print(df.head())

# # Perform operations on the DataFrame
# # For example, modifying some values
# # df.loc[df['Customer ID'] == 1, 'Call Cost'] = 'test usd$'

# # Update the Google Sheet with the modified DataFrame
# update_existing_data(df, 'Customer ID', 1, 'Call Cost', 'test usd$')

# print(df.head())


#########v2
# import gspread
# from google.oauth2.service_account import Credentials
# import pandas as pd
# import dash
# # import dash_table
# from dash import dash_table
# from dash import html
# from dash.dash_table.Format import Group

# # Create a Dash application
# app = dash.Dash(__name__)

# class GoogleSheetUpdater:
#     def __init__(self, service_account_file, document_id, sheet_index=0):
#         self.service_account_file = service_account_file
#         self.document_id = document_id
#         self.sheet_index = sheet_index
#         self.gc = self._authorize_client()
#         self.worksheet = self._open_worksheet()

#     def _authorize_client(self):
#         scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
#         credentials = Credentials.from_service_account_file(self.service_account_file, scopes=scopes)
#         return gspread.authorize(credentials)

#     def _open_worksheet(self):
#         spreadsheet = self.gc.open_by_key(self.document_id)
#         return spreadsheet.get_worksheet(self.sheet_index)

#     def get_dataframe(self):
#         records = self.worksheet.get_all_records()
#         return pd.DataFrame(records)

#     def update_existing_data(self, df, condition_col, condition_val, new_col, new_val):
#         condition_col_idx = df.columns.get_loc(condition_col) + 1
#         new_col_idx = df.columns.get_loc(new_col) + 1

#         for index, row in df.iterrows():
#             if str(row[condition_col]) == str(condition_val):
#                 try:
#                     self.worksheet.update_cell(index + 2, new_col_idx, new_val)
#                     print(f"Updated cell at row {index + 2}, column {new_col_idx} with value {new_val}.")
#                 except Exception as e:
#                     print(f"Failed to update cell at row {index + 2}, column {new_col_idx}. Error: {e}")

# # Usage
# SERVICE_ACCOUNT_FILE = './data-extraction-tool-433301-f79d60b07ff8.json'
# DOCUMENT_ID = '154VvsJcn7ZKE7mqPEIP1T-JIJbEzw4IyEExPZesa2Gc'

# updater = GoogleSheetUpdater(SERVICE_ACCOUNT_FILE, DOCUMENT_ID)
# df = updater.get_dataframe()

# print(df.head())
# # updater.update_existing_data(df, 'Customer ID', 1, 'Call Cost', 'test2 usd$')

# df = df.copy()[['Customer ID', 'Call Start time', 'Summary', 'Call Cost']]
# print(df.head())

# app.layout = html.Div([
#     html.H1("Caller Dashboard", style={'textAlign': 'center', 'color': '#003366'}),
    
#     dash_table.DataTable(
#         data=df.to_dict('records'),  # Convert DataFrame to list of dictionaries
#         columns=[{'name': col, 'id': col} for col in df.columns],
#         style_table={'overflowX': 'auto'},  # Enable horizontal scrolling
#         style_cell={
#             'textAlign': 'left',
#             'whiteSpace': 'normal',  # Allow text wrapping
#             'overflow': 'hidden',    # Hide overflowed text
#             'textOverflow': 'ellipsis',  # Optional: Add ellipsis for overflowed text
#             'padding': '10px',  # Add padding for better readability
#         },
#         style_header={
#             'backgroundColor': '#004080',  # Dark blue header
#             'color': 'white',  # White text color
#             'fontWeight': 'bold'
#         },
#         style_data={
#             'backgroundColor': '#f9f9f9',  # Light grey background for data cells
#             'color': '#333',  # Dark text color
#         },
#         style_data_conditional=[
#             {
#                 'if': {'row_index': 'odd'},
#                 'backgroundColor': '#f2f2f2'  # Alternating row colors
#             },
#             {
#                 'if': {'column_id': 'Summary'},  # Example for conditional styling on a specific column
#                 'textAlign': 'center'
#             }
#         ]
#     )
# ])

# if __name__ == '__main__':
#     app.run_server(debug=True)
##########v3
# import gspread
# from google.oauth2.service_account import Credentials
# import pandas as pd
# import dash
# from dash import dash_table, html, dcc
# from dash.dependencies import Input, Output

# # Create a Dash application
# app = dash.Dash(__name__)

# class GoogleSheetUpdater:
#     def __init__(self, service_account_file, document_id, sheet_index=0):
#         self.service_account_file = service_account_file
#         self.document_id = document_id
#         self.sheet_index = sheet_index
#         self.gc = self._authorize_client()
#         self.worksheet = self._open_worksheet()

#     def _authorize_client(self):
#         scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
#         credentials = Credentials.from_service_account_file(self.service_account_file, scopes=scopes)
#         return gspread.authorize(credentials)

#     def _open_worksheet(self):
#         spreadsheet = self.gc.open_by_key(self.document_id)
#         return spreadsheet.get_worksheet(self.sheet_index)

#     def get_dataframe(self):
#         records = self.worksheet.get_all_records()
#         return pd.DataFrame(records)

#     def update_existing_data(self, df, condition_col, condition_val, new_col, new_val):
#         condition_col_idx = df.columns.get_loc(condition_col) + 1
#         new_col_idx = df.columns.get_loc(new_col) + 1

#         for index, row in df.iterrows():
#             if str(row[condition_col]) == str(condition_val):
#                 try:
#                     self.worksheet.update_cell(index + 2, new_col_idx, new_val)
#                     print(f"Updated cell at row {index + 2}, column {new_col_idx} with value {new_val}.")
#                 except Exception as e:
#                     print(f"Failed to update cell at row {index + 2}, column {new_col_idx}. Error: {e}")


# # Usage
# SERVICE_ACCOUNT_FILE = './data-extraction-tool-433301-f79d60b07ff8.json'
# DOCUMENT_ID = '154VvsJcn7ZKE7mqPEIP1T-JIJbEzw4IyEExPZesa2Gc'

# updater = GoogleSheetUpdater(SERVICE_ACCOUNT_FILE, DOCUMENT_ID)

# app.layout = html.Div([
#     html.H1("Caller Dashboard", style={'textAlign': 'center', 'color': '#003366'}),
    
#     dash_table.DataTable(
#         id='data-table',
#         columns=[],  # Initialize empty columns
#         style_table={'overflowX': 'auto'},  # Enable horizontal scrolling
#         style_cell={
#             'textAlign': 'left',
#             'whiteSpace': 'normal',  # Allow text wrapping
#             'overflow': 'hidden',    # Hide overflowed text
#             'textOverflow': 'ellipsis',  # Optional: Add ellipsis for overflowed text
#             'padding': '10px',  # Add padding for better readability
#         },
#         style_header={
#             'backgroundColor': '#004080',  # Dark blue header
#             'color': 'white',  # White text color
#             'fontWeight': 'bold'
#         },
#         style_data={
#             'backgroundColor': '#f9f9f9',  # Light grey background for data cells
#             'color': '#333',  # Dark text color
#         },
#         style_data_conditional=[
#             {
#                 'if': {'row_index': 'odd'},
#                 'backgroundColor': '#f2f2f2'  # Alternating row colors
#             }
#         ]
#     ),
    
#     dcc.Interval(
#         id='interval-component',
#         interval=10 * 1000,  # Update every 10 seconds (adjust as needed)
#         n_intervals=0
#     )
# ])

# @app.callback(
#     Output('data-table', 'data'),
#     Output('data-table', 'columns'),
#     Input('interval-component', 'n_intervals')
# )
# def update_table(n):
#     try:
#         df = updater.get_dataframe()  # Fetch updated data
#         print("Fetched DataFrame:")
#         print(df.head())  # Print DataFrame to debug

#         updater.update_existing_data(df, 'Customer ID', 1, 'Call Cost', 'test2 usd$')

#         # Check if DataFrame is empty
#         if df.empty:
#             print("DataFrame is empty.")
#             return [], []
        
#         # Select the relevant columns
#         df = df.copy()[['Customer ID', 'Call Start time', 'Summary', 'Call Cost']]
#         print("Updated DataFrame:")
#         print(df.head())  # Print updated DataFrame
        
#         columns = [{'name': col, 'id': col} for col in df.columns]
#         data = df.to_dict('records')
#         return data, columns
#     except Exception as e:
#         print(f"Error: {e}")
#         return [], []

# if __name__ == '__main__':
#     app.run_server(debug=True)