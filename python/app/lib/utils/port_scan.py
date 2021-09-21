#!/usr/bin/env python3

import re
import nmap
import masscan
import chardet
from app.lib.utils.request import request
from app.lib.utils.finger import WhatCms, Fofa_Scanner

class Port_Scan():
    def __init__(self, mysqldb):
        self.mysqldb = mysqldb

    def get_title(self, url):

        """
        获取网站的title与banner

        :param str url: 目标url

        :return tuple title,banner: 识别的结果
        """

        title = ''
        banner = ''
        try:
            req = request.get(url)
            #获取网站的页面编码
            r_detectencode = chardet.detect(req.content)
            actual_encode = r_detectencode['encoding']
            pagecode = req.content.decode(actual_encode)
            response = re.findall('<title>(.*?)</title>', pagecode, re.S)
            if pagecode:
                #将页面解码为utf-8，获取中文标题
                if response:
                    title = response[0]
            if 'server' in req.headers.keys():
                banner = req.headers['server']
        except Exception as e:
            print(e)
        finally:
            return title, banner

    def nmap_scan(self, username, target, target_ip, scan_id, min_port, max_port):

        """
        用nmap进行扫描

        :param str username: 用户名
        :param str target: 待扫描的目标
        :param str target_ip: 待扫描的目标ip
        :param str scan_id: 扫描任务id
        :param str min_port: 扫描端口的最小值
        :param str max_port: 扫描端口的最大值

        :return list scan_list: 扫描的结果
        """
        scan_list = []
        nm = nmap.PortScanner()
        arguments = '-sS -sV -Pn -T4 --open -p %s-%s' %(min_port, max_port)
        nm.scan(hosts = target_ip, arguments = arguments)
        try:
            for host in nm.all_hosts():
                for nmap_proto in nm[host].all_protocols():
                    lport = nm[host][nmap_proto].keys()
                    lport = sorted(lport)
                    for nmap_port in lport:
                        protocol = nm[host][nmap_proto][int(nmap_port)]['name']
                        product = nm[host][nmap_proto][int(nmap_port)]['product']
                        version = nm[host][nmap_proto][int(nmap_port)]['version']
                        if 'tcpwrapped' not in protocol:
                            if 'http' in protocol or protocol == 'sun-answerbook':
                                if protocol == 'https' or protocol == 'https-alt':
                                    scan_url_port = 'https://' + str(host) + ':' + str(nmap_port)
                                else:
                                    scan_url_port = 'http://' + str(host) + ':' + str(nmap_port)
                                
                                finger_data = self.mysqldb.all_finger(username, '0')
                                cms = Fofa_Scanner(target, finger_data['fofa_cms'])
                                fofa_finger = cms.run()
                                cms_name = ''
                                cms_name_flag = 0
                                for fofa_finger_tmp in fofa_finger:
                                    if fofa_finger_tmp.lower() in cms.cms_finger_list:
                                        cms_name = fofa_finger_tmp
                                        cms_name_flag = 1
                                
                                if not cms_name_flag:
                                    whatcms = WhatCms(target, finger_data['cms'])
                                    result = whatcms.run()
                                    cms_name = ''
                                    if result:
                                        cms_name = result['cms_name']

                                result = self.get_title(scan_url_port)
                                self.mysqldb.save_target_port(username, target, scan_id, target_ip, str(nmap_port), cms_name, protocol, product, version, result[0], result[1])
                                self.mysqldb.save_port(username, target, scan_url_port, target_ip, str(nmap_port), cms_name, protocol, product, version, result[0], result[1])
                            else:
                                scan_url_port = str(host) + ':' + str(nmap_port)
                                self.mysqldb.save_target_port(username, target, scan_id, target_ip, str(nmap_port), '', protocol, product, version, '', '')
                                self.mysqldb.save_port(username, target, scan_url_port, target_ip, str(nmap_port), '', protocol, product, version, '', '')
                            
                            scan_list.append(scan_url_port)
        except Exception as e:
            print(e)
            pass
        finally:
            pass
        return scan_list

    def masscan_scan(self, username, target, target_ip, scan_id, min_port, max_port, rate):
        
        """
        用masscan进行扫描

        :param str username: 用户名
        :param str target: 待扫描的目标
        :param str target_ip: 待扫描的目标
        :param str scan_id: 扫描id
        :param str min_port: 扫描端口的最小值
        :param str max_port: 扫描端口的最大值
        :param str rate: 扫描速率

        :return list scan_list: 扫描的结果
        """

        scan_list = []
        print('Masscan starting.....\n')
        masscan_scan = masscan.PortScanner()
        masscan_scan.scan(hosts = target_ip, ports='%s-%s'%(min_port, max_port), arguments = '-sS -Pn -n --randomize-hosts -v --send-eth --open --rate %s' % (rate))
        try:
            for host in masscan_scan.all_hosts:
                for masscan_proto in masscan_scan[host].keys():
                    for masscan_port in masscan_scan[host][masscan_proto].keys():
                        nm = nmap.PortScanner()
                        arguments = '-p %s -sS -sV -Pn -T4 --open' % (masscan_port)
                        nm.scan(hosts = host, arguments = arguments)
                        for nmap_proto in nm[host].all_protocols():
                            protocol = nm[host][nmap_proto][int(masscan_port)]['name']
                            product = nm[host][nmap_proto][int(masscan_port)]['product']
                            version = nm[host][nmap_proto][int(masscan_port)]['version']
                            if 'tcpwrapped' not in protocol:
                                if 'http' in protocol or protocol == 'sun-answerbook':
                                    if protocol == 'https' or protocol == 'https-alt':
                                        scan_url_port = 'https://' + str(host) + ':' + str(masscan_port)
                                    else:
                                        scan_url_port = 'http://' + str(host) + ':' + str(masscan_port)
                                    
                                    finger_data = self.mysqldb.all_finger(username, '0')
                                    cms = Fofa_Scanner(target, finger_data['fofa_cms'])
                                    fofa_finger = cms.run()
                                    cms_name = ''
                                    cms_name_flag = 0
                                    for fofa_finger_tmp in fofa_finger:
                                        if fofa_finger_tmp.lower() in cms.cms_finger_list:
                                            cms_name = fofa_finger_tmp
                                            cms_name_flag = 1
                                    
                                    if not cms_name_flag:
                                        whatcms = WhatCms(target, finger_data['cms'])
                                        result = whatcms.run()
                                        cms_name = ''
                                        if result:
                                            cms_name = result['cms_name']

                                    result = self.get_title(scan_url_port)
                                    self.mysqldb.save_target_port(username, target, scan_id,  target_ip, str(masscan_port), cms_name, protocol, product, version, result[0], result[1])
                                    self.mysqldb.save_port(username, target, scan_url_port, target_ip, str(masscan_port), cms_name, protocol, product, version, result[0], result[1])
                                else:
                                    scan_url_port = str(host) + ':' + str(masscan_port)
                                    self.mysqldb.save_target_port(username, target, scan_id, target_ip, str(masscan_port), '', protocol, product, version, '', '')
                                    self.mysqldb.save_port(username, target, scan_url_port, target_ip, str(masscan_port), '', protocol, product, version, '', '')
                                    scan_list.append(scan_url_port)

            print('Masscan scanned.....\n')
        except Exception as e:
            print(e)
            pass
        finally:
            pass
        return scan_list

if __name__ == '__main__':
    port_scan = Port_Scan()
    port_scan.masscan_scan('127.0.0.1')