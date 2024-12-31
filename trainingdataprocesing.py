import json

def parse_chat_log(input_file, output_file):
    """
    Parses ChatGPT-style logs into JSON training data.
    Handles unhandled lines by treating them as user input.
    Replaces instances of "content removed" with "N/A."
    Removes single string entries like "2/2" that might affect input processing.

    Args:
        input_file (str): Path to the chat log file.
        output_file (str): Path to save the JSON training data.
    """
    training_data = []
    current_user_input = None
    current_bot_response = []
    is_capturing_bot_response = False

    # Debugging counters
    total_user_inputs = 0
    total_bot_responses = 0
    skipped_lines = 0
    placeholder_added = 0
    skipped_strings = []

    try:
        # Open and read the file, removing blank lines and trimming whitespace
        with open(input_file, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]

        print(f"Total lines after removing blanks: {len(lines)}")

        for i, line in enumerate(lines):
            # Replace instances of "content removed" with "N/A"
            if "content removed" in line.lower():
                line = "N/A"

            # Skip lines that are single strings like "2/2"
            if len(line.split()) == 1 and "/" in line:
                print(f"[INFO] Line {i}: Skipping single string line: {line}")
                skipped_lines += 1
                skipped_strings.append((i, line, lines[i + 1] if i + 1 < len(lines) else "N/A"))
                continue

            if line.startswith("You said:"):
                total_user_inputs += 1  # Count user inputs

                # Save the previous pair before starting a new one
                if current_user_input and current_bot_response:
                    training_data.append({
                        "user_input": "N/A" if "content removed" in current_user_input.lower() else current_user_input,
                        "response": "\n".join(current_bot_response)
                    })
                    current_bot_response = []  # Reset bot response

                # Capture new user input
                current_user_input = line[len("You said:"):].strip()
                is_capturing_bot_response = False
                print(f"[DEBUG] Line {i}: Captured user input: {current_user_input}")

            elif line.startswith("ChatGPT said:"):
                total_bot_responses += 1  # Count bot responses

                if current_user_input is None:
                    # Orphan bot response detected
                    print(f"[WARNING] Line {i}: Bot response found without a preceding user input. Adding placeholder.")
                    training_data.append({
                        "user_input": "N/A",
                        "response": line[len("ChatGPT said:"):].strip()
                    })
                    placeholder_added += 1
                    current_bot_response = []  # Reset bot response
                    continue

                # Start capturing bot response
                is_capturing_bot_response = True
                print(f"[DEBUG] Line {i}: Starting new bot response block.")

            elif is_capturing_bot_response:
                # Append to bot response if within response block
                current_bot_response.append(line)
                print(f"[DEBUG] Line {i}: Appended to bot response: {line}")

            else:
                # Treat unhandled line as a new user input
                print(f"[INFO] Line {i}: Treating unhandled line as user input: {line}")
                if current_user_input and current_bot_response:
                    # Save current pair before starting a new one
                    training_data.append({
                        "user_input": "N/A" if "content removed" in current_user_input.lower() else current_user_input,
                        "response": "\n".join(current_bot_response)
                    })
                    current_bot_response = []  # Reset bot response

                # Use unhandled line as new user input
                current_user_input = line
                total_user_inputs += 1
                is_capturing_bot_response = False

        # Save the last user-bot pair, if any
        if current_user_input and current_bot_response:
            training_data.append({
                "user_input": "N/A" if "content removed" in current_user_input.lower() else current_user_input,
                "response": "\n".join(current_bot_response)
            })
        elif current_user_input and not current_bot_response:
            # Add placeholder for missing bot response
            training_data.append({
                "user_input": "N/A" if "content removed" in current_user_input.lower() else current_user_input,
                "response": "N/A"
            })
            placeholder_added += 1

        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as out_file:
            json.dump(training_data, out_file, indent=4, ensure_ascii=False)

        print(f"Training data successfully saved to {output_file}")
        print(f"Total user-bot pairs: {len(training_data)}")
        print(f"Total user inputs: {total_user_inputs}")
        print(f"Total bot responses: {total_bot_responses}")
        print(f"Skipped single-string lines: {skipped_lines}")

        if skipped_strings:
            print("[INFO] Skipped lines with potential related inputs:")
            for index, skipped, next_line in skipped_strings:
                print(f"  Line {index}: Skipped '{skipped}' -> Next line: '{next_line}'")

    except FileNotFoundError:
        print(f"[ERROR] Input file not found: {input_file}")
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}")

# Example usage
if __name__ == "__main__":
    input_file = "pretraining.txt"  # Replace with your input file name
    output_file = "training_data.json"  # Replace with your desired output file name
    parse_chat_log(input_file, output_file)