import asyncio
import serial_asyncio
import sys

async def uart_receiver(reader):
    """异步UART接收协程"""
    while True:
        try:
            data = await reader.read(100)  # 每次最多读取100字节
            if data:
                try:
                    print("接收: ", data.decode('utf-8'), end='')
                except UnicodeDecodeError:
                    print("接收 (原始数据): ", data)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"接收错误: {e}")
            break

async def uart_sender(writer):
    """异步UART发送协程"""
    loop = asyncio.get_running_loop()
    while True:
        try:
            # 使用run_in_executor避免阻塞事件循环
            message = await loop.run_in_executor(
                None, 
                input, 
                "请输入要发送的消息 (输入 'exit' 退出): "
            )
            
            if message.lower() == 'exit':
                break
                
            writer.write(message.encode('utf-8') + b'\n')
            await writer.drain()  # 等待数据发送完成
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"发送错误: {e}")
            break

async def main():
    """主协程"""
    try:
        # 创建异步串口连接
        reader, writer = await serial_asyncio.open_serial_connection(
            url='COM3',
            baudrate=115200,
            timeout=1
        )
        
        print(f"已连接到 COM3, 波特率 115200")
        
        # 创建接收任务
        receiver_task = asyncio.create_task(uart_receiver(reader))
        
        # 运行发送协程
        await uart_sender(writer)
        
        # 取消接收任务
        receiver_task.cancel()
        try:
            await receiver_task
        except asyncio.CancelledError:
            pass
            
    except serial_asyncio.serial.SerialException as e:
        print(f"串口错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if 'writer' in locals():
            writer.close()
            await writer.wait_closed()
        print("程序结束")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)