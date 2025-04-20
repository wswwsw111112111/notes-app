from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])

def index():
    if request.method == 'POST':
        # 获取用户输入的文本或图片
        text = request.form.get('text')
        image = request.files.get('image')
        # 处理用户输入的文本或图片
        # ...

    return '''
    <form method="POST" enctype="multipart/form-data">
        <textarea name="text" placeholder="请输入文本"></textarea><br>
        <input type="file" name="image"><br>
        <input type="submit" value="提交">
    </form>
    '''

if __name__ == '__main__':
    app.run()