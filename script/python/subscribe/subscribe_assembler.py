import requests
from flask import Flask, make_response

subscribe_coll = [
    {
        "url": "https://example.com/link1",
        "alias": "alias"
    },
]

app = Flask(__name__)


@app.route('/subscribe')
def subscribe():
    subscribe_assembler = ""
    upload = 0
    download = 0
    total = 0

    for subscribe in subscribe_coll:
        try:
            response = requests.get(subscribe['url'], timeout=10)
            response.raise_for_status()

            # Process the response text
            lines = response.text.split('\n')
            processed_lines = []
            for index, line in enumerate(lines):
                # 跳过第1行处理
                if index <= 1:
                    processed_lines.append(line)
                    continue
                if line.strip():
                    parts = line.split('#', 1)
                    if len(parts) > 1:
                        protocol = parts[0].split('://', 1)[0]  # Get the protocol
                        new_alias = f"{subscribe['alias']}-{protocol}-{index - 1}"
                        processed_line = f"{parts[0]}#{new_alias}"
                    else:
                        processed_line = line
                    processed_lines.append(processed_line)

            subscribe_assembler += '\n'.join(processed_lines) + "\n"

            # Process user info
            userinfo = response.headers.get('Subscription-Userinfo', '')
            if userinfo:
                info_parts = userinfo.split(';')
                upload += int(info_parts[0].split('=')[1])
                download += int(info_parts[1].split('=')[1])
                total += int(info_parts[2].split('=')[1])

        except requests.RequestException as e:
            print(f"Error fetching subscription data from {subscribe['url']}: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred while processing {subscribe['url']}: {str(e)}")

    response = make_response(subscribe_assembler.strip())
    response.headers[
        'Subscription-Userinfo'] = f'upload={upload};download={download};total=3221225472000;expire=2588803200'
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9679)