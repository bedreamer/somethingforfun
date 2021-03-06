# -*- coding: utf8 -*-
import socket
import time
import select
import sys
import json


class HttpRule:
    def __init__(self, path, callback, content):
        self.path = path
        self.callback = callback
        self.content = content

    def is_match(self, path):
        if self.path == path:
            return True

        return False

    def do_callback(self, request, ack):
        return self.callback(self.path, request, ack)


class HttpAck:
    def __init__(self, session, request, route):
        self.headers = {}
        self.ack_done = False
        self.request = request
        self.route = route
        self.body = None
        self.http_head_done = False
        self.user = {}
        self.EOH = '\r\n'

    # 获取状态。
    def get_http_header(self, rule, code, status):
        header = 'HTTP/1.1 %d %s\r\n' % (code, status)

        if rule is not None:
            self.headers['Content-Type'] = rule.content

        for key in self.headers:
            header = header + '%s: %s\r\n' % (key, self.headers[key])

        if 'Server' not in self.headers:
            header = header + 'Server: TinyHttpServer 1.0 By LiJie\r\n'
        if 'Content-Type' not in self.headers:
            header = header + 'Content-Type: text/html; charset=utf-8\r\n'
        if 'Date' not in self.headers:
            header = header + 'Date: %s\r\n' % time.ctime()
        if 'Cache-Control' not in self.headers:
            header = header + 'Cache-Control: no-cache\r\n'

        header = header

        return header

    # 返回异常状态
    def return_unormal(self, code, status):
        self.ack_done = True
        self.http_head_done = True
        return self.get_http_header(None, code, status) + self.EOH

    # 返回正常状态
    def return_normal(self, user_ack_data):
        http_head = ''
        if self.http_head_done is False:
            self.http_head_done = True
            http_head = self.get_http_header(None, 200, 'OK')

        body = user_ack_data
        return http_head + self.EOH + body

    '''
        ack 是字典结构
        ack中的 ‘done’， 字段默认为True，即若返回非None字典，则表明应答处理完成。
        ack中的 ’code‘， 字段默认为 200，
        ack中的 ‘status’，字段默认为 OK
        ack中的 ‘Server’，字段默认为 TinyHttpServer
        ack中的 ’Content-Type‘，字段默认为：text/html; charset=utf-8
    '''
    def process_ack(self):
        for rule in self.route:
            if rule.is_match(self.request.path) is False:
                continue

            ack_data = rule.callback(self.request.path, self.request, self)
            if ack_data is None:
                return None

            # 如果返回字符串也认为是有效返回
            if type(ack_data) == type('str'):
                ack_data = {'body': ack_data}

            if type(ack_data) != type({}):
                return self.return_unormal(503, 'Internal error')

            ack_done = True
            code = 200
            status = 'OK'
            http_ack_header = ''
            ack = ''
            http_ack_body = ''
            if 'done' in ack_data:
                if ack_data['done'] != False and ack_data['done'] != True:
                    return self.return_unormal(503, 'Internal error')
                else:
                    ack_done = ack_data['done']

            # 无论是什么状态，若HTTP头部未准备好则处理头部。
            # 头部准备好的条件是：ack_done为True或字段中出现body
            if self.http_head_done is False:
                if 'code' in ack_data:
                    code = ack_data['code']
                if 'status' in ack_data:
                    status = ack_data['status']
                http_ack_header = self.get_http_header(rule, code, status)

                if ack_done is True:
                    self.http_head_done = True
                if 'body' in ack_data:
                    self.http_head_done = True

            # 处理应答完成标识
            if ack_done is True:
                self.ack_done = True

            if 'body' in ack_data:
                http_ack_body = ack_data['body']

            if self.http_head_done is True:
                http_ack_header = http_ack_header + self.EOH

            if len(http_ack_header) + len(http_ack_body):
                return http_ack_header + http_ack_body
            else:
                # may data not ready.
                return None

        return self.return_unormal(404, 'Not Found!')

class HttpRequest:
    def __init__(self, session):
        self.lines = []

        # HTTP请求头部接受完成标识
        self.header_done = False
        # HTTP请求接收完成
        self.request_done = False

        self.body = ''
        self.method = None
        self.url = None
        self.path = None
        self.query_string = None
        self.query = None
        self.request_version = None
        self.heads = None
        self.form = None

    # 如果需要退出会话，返回True
    def first_line_ready(self, first_line):
        first_line = first_line.replace('\r\n', '')
        first_line = first_line.replace('\t', ' ')
        first_line = first_line.split(' ')
        if '' in first_line:
            first_line = first_line.remove('')

        # invalid request header
        if len(first_line) != 3:
            return True

        self.method = first_line[0].upper()
        self.url = first_line[1]
        self.request_version = first_line[2].upper()

        if '?' in self.url:
            split = self.url.index('?')
            self.path = self.url[:split]
            self.query_string = self.url[split:]
            self.query = {}
        else:
            self.path = self.url
            self.query_string = ''
            self.query = {}

        return False

    # 如果需要退出会话，返回True
    def all_headers_ready(self, headers):
        self.header_done = True
        self.heads = {}
        if self.method == 'GET':
            self.request_done = True

        headers = headers.split('\r\n')

        for head in headers:
            # 处理到最后一个字段
            if head == '':
                break

            if ':' not in head:
                return True
            split = head.index(':')
            key = head[:split]
            val = head[split + 1:]
            self.heads[ key ] = val

        return False

    # 如果需要退出会话，返回True
    def about_more_data(self):
        if self.method == 'POST' and len(self.body) >= int(self.heads['Content-Length']):
            self.request_done = True
            self.form = self.body

        return False

    # 如果需要退出会话，返回True
    def process_request(self, data):
        self.body = self.body + data
        if self.method is None:
            split_position = self.body.index('\r\n')
            if split_position >= 0:
                # 提取第一行
                first_line = self.body[:split_position + 2]
                self.body = self.body[split_position + 2:]

                if True == self.first_line_ready(first_line):
                    return True

        if self.header_done is False:
            if '\r\n\r\n' in self.body:
                header_split_position = self.body.index('\r\n\r\n')
            else:
                return False

            if header_split_position < 0:
                return False

            # 获取全部有效的请求头部
            headers = self.body[:header_split_position + 4]
            self.body = self.body[header_split_position + 4:]

            if True == self.all_headers_ready(headers):
                return True

        if len(self.body) > 0:
            return self.about_more_data()
        else:
            return False

class HttpConnection:
    def __init__(self, session, route):
        self.session = session
        self.route = route

        self.http_request = HttpRequest(self)
        self.http_ack = None

        self.request_done = False
        self.request_broken = False
        self.ack_done = False
        self.ack_broken = False
        self.process_done = False

    def do_request(self):
        handle = self.session.handle
        try:
            data = handle.recv(1024)
            #print '<', data, '>'
        except Exception,e:
            self.request_broken = True
            return

        if data is None or len(data) == 0:
            self.request_broken = True
        else:
            self.request_broken = self.http_request.process_request(data)

    def do_ack(self):
        if self.http_ack is None:
            self.http_ack = HttpAck(self, self.http_request, self.route)

        data = self.http_ack.process_ack()
        if data is not None and len(data) > 0:
            handle = self.session.handle
            try:
                handle.send(data)
            except Exception, e:
                self.ack_broken = True
                return

    # 判断是否接收到完整的HTTP请求
    def is_request_done(self):
        return self.http_request.request_done

    # 判断HTTP请求是否有效
    def is_request_broken(self):
        return self.request_broken

    def is_ack_done(self):
        if self.http_ack is not None:
            return self.http_ack.ack_done

        return False

    def is_ack_broken(self):
        return self.ack_broken

    def is_process_done(self):
        return self.process_done


class HttpSession:
    # 会话需要等待接收数据
    SESSION_WAIT_DATA=1
    # 会话需要发送数据
    SESSION_PATCH_DATA=2
    # 会话等待数据发送完成
    SESSION_WAIT_DONE=3
    # 会话等待结束
    SESSION_WAIT_DESTROY=4

    def __init__(self, route, handle, addr):
        self.handle = handle
        self.addr = addr
        self.born_tsp = time.time()
        self.last_heartbeat = time.time()
        self.status = self.SESSION_WAIT_DATA
        self.connection = HttpConnection(self, route)

    # 等待HTTP请求发送完成
    def pending_with_http_request(self, rl):
        if self.handle in rl:
            # 使用链接执行请求处理
            self.connection.do_request()

        # HTTP请求数据接收完成
        if self.connection.is_request_done() is True:
            return self.SESSION_PATCH_DATA

        # HTTP请求无效, 直接关闭连接
        if self.connection.is_request_broken() is True:
            return self.SESSION_WAIT_DESTROY

        # HTTP请求在3600秒内没有完成, 则关闭链接
        if time.time() - self.last_heartbeat > 3600:
            return self.SESSION_WAIT_DESTROY

        return self.SESSION_WAIT_DATA

    # 等待http应答完成
    def pending_with_http_ack(self, wl):
        if self.handle in wl:
            # 执行应答
            self.connection.do_ack()

        # HTTP请求数据接收完成
        if self.connection.is_ack_done():
            return self.SESSION_WAIT_DONE

        # HTTP请求数据应答错误
        if self.connection.is_ack_done():
            return self.SESSION_WAIT_DESTROY

        return self.SESSION_PATCH_DATA

    # 等待http处理过程完成
    def pending_with_process_done(self):
        # 执行应答
        if self.connection.is_process_done() is True:
            return self.SESSION_WAIT_DESTROY

        return self.SESSION_WAIT_DONE

    # 返回None, 结束会话
    def step_forward(self, rl, wl, el):
        if self.status == self.SESSION_WAIT_DATA:
            self.status = self.pending_with_http_request(rl)

        # 若请求完成则可以立即处理
        if self.status == self.SESSION_PATCH_DATA:
            self.status = self.pending_with_http_ack(wl)

        if self.status == self.SESSION_WAIT_DONE:
            if self.handle in wl:
                self.status = self.SESSION_WAIT_DESTROY

        if self.status == self.SESSION_WAIT_DESTROY:
            return None

        return False

    # 判定会话是否需要读数据
    def need_read(self):
        if self.status == self.SESSION_WAIT_DATA:
            return True
        else:
            return False

    # 判定会话是否需要写数据
    def need_write(self):
        if self.status == self.SESSION_PATCH_DATA:
            return True
        elif self.status == self.SESSION_WAIT_DONE:
            return True
        else:
            return False

    # 结束会话，释放会话的资源
    def shut_down(self):
        self.handle.close()


class TinyHttpdServer:
    def __init__(self, server_port, debug=None):
        if debug is None:
            debug = False

        # 调试信息输出开关
        self.debug_on = debug

        self.server_port = server_port
        # all http connection session
        self.sessions = []
        self.routes = []

        self.server_handle = socket.socket()
        self.server_handle.bind(('0.0.0.0', self.server_port))
        self.server_handle.listen(1)
        self.server_handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

        # 注册连接信息
        self.route('/httpd/connections.json', self.connection_statistics)

    # 统计所有连接信息
    def connection_statistics(self, path, request, ack):
        j = []
        for s in self.sessions:
            j.append({'conn': repr(s.addr), 'tsp': s.born_tsp, 'last': s.last_heartbeat})
            ack.headers['Content-Type'] = 'application/json'

        return json.dumps(j)

    def debug(self, e):
        if self.debug_on is True:
            print e

    # 添加一个路由
    def route(self, path, callback, content=None):
        if content is None:
            content = 'text/html; charset=utf-8'
        r = HttpRule(path, callback, content)
        self.routes.append(r)

    # 安装所有有效的可用与select操作的描述符
    def static_setup_selector(self):
        r, w = [self.server_handle], []
        for session in self.sessions:
            if session.need_read() is True:
                r.append(session.handle)
            if session.need_write() is True:
                w.append(session.handle)

        return r, w, []

    # 处理新链接
    def static_new_connection(self):
        conn, addr = self.server_handle.accept()
        session = HttpSession(self.routes, conn, addr)
        self.sessions.append(session)
        print 'new connection:', addr

    # 单步执行服务
    def step_forward(self, ttl):
        rl, wl, el = self.static_setup_selector()
        try:
            r, w, _ = select.select(rl, wl, el, ttl)
        except Exception, e:
            self.debug(e)

        # 处理新连接
        if self.server_handle in r:
            self.static_new_connection()

        # 处理已有会话
        i = 0
        while i < len(self.sessions):
            session = self.sessions[i]
            status = session.step_forward(r, w, [])
            if status == None:
                session.shut_down()
                self.sessions[i] = None

            i = i + 1

        # 删除已经关闭的会话
        while None in self.sessions:
            self.sessions.remove(None)

        # never exit.
        return False

    def shut_down(self):
        self.server_handle.close()


