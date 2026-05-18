# 主入口文件
import uvicorn
from Backend.app import create_app

# 创建 FastAPI 应用实例
app = create_app()

# 主程序入口
if __name__ == "__main__":
    # 运行 FastAPI 应用，监听 127.0.0.1:8080
    uvicorn.run("Backend.main:app", host="0.0.0.0", port=8080, reload=True)
