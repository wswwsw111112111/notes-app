from PIL import Image, ImageDraw, ImageFont

# 创建一个64x64的彩色图标
img = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)

# 绘制一个彩色笔记本图标
# 笔记本主体 - 蓝色
draw.rounded_rectangle([10, 10, 54, 54], radius=5, fill='#4A90E2')

# 笔记本线条 - 白色
for y in [22, 30, 38, 46]:
    draw.rectangle([18, y, 46, y+2], fill='white')

# 笔记本螺旋 - 橙色
for x in [16, 24, 32, 40, 48]:
    draw.ellipse([x-2, 8, x+2, 12], fill='#FF9500')

img.save('favicon.png')
print("PNG图标已生成，请用在线工具转换为.ico")