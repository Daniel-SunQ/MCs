import asyncio
import json
from datetime import datetime
import aioconsole  # 用于异步控制台输入
import socketio  # 添加socketio导入

# 模拟器配置
HOST = 'localhost'
PORT = 5001
APP_SERVER_URL = 'http://localhost:8080'  # app.py的地址

# 创建socketio客户端
sio = socketio.AsyncClient()

# 全局状态
vehicle_state = {
    'speed': 0.0,          # 速度 (km/h)
    'direction': 'straight',  # 方向
    'gear': 'P',           # 档位 (P/R/N/D)
    'lights': {
        'left_turn': False,   # 左转向灯
        'right_turn': False,  # 右转向灯
        'high_beam': False,   # 远光灯
        'low_beam': False,    # 近光灯
        'position': False,    # 位置灯
        'fog': False,         # 雾灯
        'warning': False      # 警示灯
    },
    'engine_temp': 25.0,   # 发动机温度 (°C)
    'fuel_level': 100.0    # 油量百分比
}

# 添加socketio事件处理器
@sio.event
async def vehicle_status_update(data):
    """处理来自app.py的状态更新"""
    
    status = data['status']
    # 更新档位
    if 'gear' in status:
        vehicle_state['gear'] = status['gear']
        print(f"档位已更新为: {status['gear']}")
    
    # 更新灯光状态
    if 'lights' in status:
        # 将灯光数组转换为字典格式
        new_lights = {
            'left_turn': False,
            'right_turn': False,
            'high_beam': False,
            'low_beam': False,
            'position': False,
            'fog': False,
            'warning': False,
        }
        for light in status['lights']:
            light_name = light.replace('-', '_')
            new_lights[light_name] = True
        
        vehicle_state['lights'] = new_lights
        print(f"灯光状态已更新: ")
        for light in new_lights:
            print(f"{light}: {new_lights[light]}")



class VehicleSimulator:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not hasattr(cls, '_instance') or cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        if not hasattr(self.__class__, '_instance') or self.__class__._instance is None:
            self.__class__._instance = self
        self.clients = set()
        self.is_running = True
        self.last_state = None
        print("""
模拟器命令格式说明：
1. 速度控制：speed <value>     (例: speed 60)
2. 方向控制：turn <left/right/straight>
3. 档位控制：gear <P/R/N/D>
4. 灯光控制：
   - light left_turn <on/off>
   - light right_turn <on/off>
   - light high_beam <on/off>
   - light low_beam <on/off>
   - light position <on/off>
   - light fog <on/off>
   - light warning <on/off>
5. 发动机温度：temp <value>    (例: temp 75)
6. 油量控制：fuel <value>      (例: fuel 80)
7. 退出程序：exit

示例：
speed 60          # 设置速度为60km/h
turn left         # 左转
gear D            # 切换到D档
light high_beam on # 打开远光灯
""")

    async def handle_client(self, reader, writer):
        """处理客户端连接"""
        print(f"新客户端连接: {writer.get_extra_info('peername')}")
        self.clients.add(writer)
        
        try:
            while self.is_running:
                try:
                    data = await reader.read(1024)
                    if not data:
                        break
                    
                    command = json.loads(data.decode())
                    self.process_command(command)
                    
                except json.JSONDecodeError:
                    print("收到无效的JSON数据")
                except Exception as e:
                    print(f"处理客户端数据时出错: {e}")
                    break
        finally:
            self.clients.remove(writer)
            writer.close()
            await writer.wait_closed()
            print(f"客户端断开连接: {writer.get_extra_info('peername')}")

    def process_command(self, command):
        """处理接收到的命令"""
        if command.get('type') == 'control':
            action = command.get('action', '')
            if action == 'turn_left':
                vehicle_state['direction'] = 'left'
                vehicle_state['lights']['left_turn'] = True
            elif action == 'turn_right':
                vehicle_state['direction'] = 'right'
                vehicle_state['lights']['right_turn'] = True
            elif action == 'speed_up':
                vehicle_state['speed'] = min(vehicle_state['speed'] + 5, 200)
            elif action == 'speed_down':
                vehicle_state['speed'] = max(vehicle_state['speed'] - 5, 0)
            
            # 处理命令后立即广播状态
            asyncio.create_task(self.broadcast_state(force=True))
    
    def state_has_changed(self):
        """检查状态是否发生变化"""
        current_state = {
            'speed': vehicle_state['speed'],
            'direction': vehicle_state['direction'],
            'gear': vehicle_state['gear'],
            'lights': vehicle_state['lights'].copy(),
            'engine_temp': vehicle_state['engine_temp'],
            'fuel_level': vehicle_state['fuel_level']
        }
        
        if self.last_state != current_state:
            self.last_state = current_state.copy()
            return True
        return False
    
    async def broadcast_state(self, force=False):
        """广播车辆状态到所有连接的客户端"""
        if self.clients and (force or self.state_has_changed()):
            state_data = {
                'timestamp': datetime.now().isoformat(),
                'state': vehicle_state
            }
            message = json.dumps(state_data).encode()
            
            for writer in list(self.clients):
                try:
                    writer.write(message)
                    await writer.drain()
                except Exception as e:
                    print(f"发送状态更新时出错: {e}")
                    self.clients.remove(writer)
                    writer.close()
    
    async def handle_console_input(self):
        """处理控制台输入"""
        while self.is_running:
            try:
                # 异步读取控制台输入
                command = await aioconsole.ainput('> ')
                if not command:
                    continue

                parts = command.lower().split()
                if not parts:
                    continue

                state_changed = False

                if parts[0] == 'exit':
                    print("正在退出模拟器...")
                    self.is_running = False
                    break

                elif parts[0] == 'speed' and len(parts) == 2:
                    try:
                        speed = float(parts[1])
                        vehicle_state['speed'] = max(0, min(200, speed))
                        print(f"速度已设置为: {vehicle_state['speed']} km/h")
                        state_changed = True
                    except ValueError:
                        print("无效的速度值")

                elif parts[0] == 'turn' and len(parts) == 2:
                    print(f"方向已设置为: {parts[1]}")
                    print(f"parts: {parts}")
                    if parts[1] in ['left', 'right', 'straight']:
                        vehicle_state['direction'] = parts[1]
                        # 自动处理转向灯
                        vehicle_state['lights']['left_turn'] = (parts[1] == 'left')
                        vehicle_state['lights']['right_turn'] = (parts[1] == 'right')
                        print(f"方向已设置为: {parts[1]}")
                        state_changed = True
                    else:
                        print("无效的方向值 (使用 left/right/straight)")

                elif parts[0] == 'gear' and len(parts) == 2:
                    if parts[1].upper() in ['P', 'R', 'N', 'D']:
                        vehicle_state['gear'] = parts[1].upper()
                        print(f"档位已设置为: {vehicle_state['gear']}")
                        state_changed = True
                    else:
                        print("无效的档位 (使用 P/R/N/D)")

                elif parts[0] == 'light' and len(parts) == 3:
                    light_name = parts[1]
                    if light_name in vehicle_state['lights']:
                        if parts[2] in ['on', 'off']:
                            vehicle_state['lights'][light_name] = (parts[2] == 'on')
                            print(f"{light_name} 已设置为: {parts[2]}")
                            state_changed = True
                        else:
                            print("无效的灯光状态 (使用 on/off)")
                    else:
                        print("无效的灯光名称")

                elif parts[0] == 'temp' and len(parts) == 2:
                    try:
                        temp = float(parts[1])
                        vehicle_state['engine_temp'] = max(0, min(150, temp))
                        print(f"发动机温度已设置为: {vehicle_state['engine_temp']}°C")
                        state_changed = True
                    except ValueError:
                        print("无效的温度值")

                elif parts[0] == 'fuel' and len(parts) == 2:
                    try:
                        fuel = float(parts[1])
                        vehicle_state['fuel_level'] = max(0, min(100, fuel))
                        print(f"油量已设置为: {vehicle_state['fuel_level']}%")
                        state_changed = True
                    except ValueError:
                        print("无效的油量值")

                else:
                    print("无效的命令格式")

                if state_changed:
                    await self.broadcast_state(force=True)

            except Exception as e:
                print(f"处理输入时出错: {e}")

    async def start(self):
        """启动模拟器"""
        # 连接到app.py服务器
        try:
            await sio.connect(APP_SERVER_URL)
            print(f"已连接到应用服务器: {APP_SERVER_URL}")
        except Exception as e:
            print(f"连接到应用服务器失败: {e}")

        server = await asyncio.start_server(
            self.handle_client, HOST, PORT
        )
        
        addr = server.sockets[0].getsockname()
        print(f'模拟器服务器运行在 {addr}')
        
        async with server:
            await asyncio.gather(
                server.serve_forever(),
                self.handle_console_input(),
                # self.periodic_state_broadcast()
            )
    
    def stop(self):
        """停止模拟器"""
        self.is_running = False
        # 断开与app.py的连接
        asyncio.create_task(sio.disconnect())

    # async def periodic_state_broadcast(self):
    #     """定期广播状态"""
    #     while self.is_running:
    #         await self.broadcast_state()
    #         await asyncio.sleep(1)  # 每秒广播一次状态

async def main():
    """主函数"""
    simulator = VehicleSimulator()
    try:
        await simulator.start()
    except KeyboardInterrupt:
        print("\n正在停止模拟器...")
        simulator.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n模拟器已停止") 