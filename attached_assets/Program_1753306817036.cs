using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.IO;
using System.Collections.Generic;
using System.Configuration;
using Microsoft.Practices.Unity;
using AutoMapper;
using RastreioFacil.Domain.Entities;
using RastreioFacil.Domain.DTO;
using RastreioFacil.Domain.Interfaces.Services;
using RastreioFacil.Gateway.Mappers;

namespace RastreioFacil.Gateway
{
    class Program : Parameters
    {
        private static readonly ManualResetEvent allDone = new ManualResetEvent(false);
        private static readonly byte[] bytes = new Byte[999999999];
        private static readonly List<Socket> cleintSocket = new List<Socket>();
        private static Socket listener;

        private readonly IDadosVeiculoServices dadosVeiculos;

        private readonly IVeiculoServices veiculos;

        private readonly IMensagemServices mensagem;


        public Program()
        {
            IoC.IoC.Resolve(Container);
            dadosVeiculos = Container.Resolve<IDadosVeiculoServices>();
            veiculos = Container.Resolve<IVeiculoServices>();
            mensagem = Container.Resolve<IMensagemServices>();
        }


        static void Main(string[] args)
        {
            Console.Title = "Gateway - RastreiFacil";
            AutoMapperConfig.RegisterMappings();
            StartListening();
        }


        private static void StartListening()
        {
            var host = Dns.GetHostEntry(Dns.GetHostName());
            IPAddress ipAddress = null;
            foreach (var ip in host.AddressList)
            {
                if (ip.AddressFamily == AddressFamily.InterNetwork)
                {
                    ipAddress = ip;
                }
            }

            IPHostEntry ipHostInfo = Dns.GetHostEntry(Dns.GetHostName());
            IPEndPoint localEndPoint = new IPEndPoint(ipAddress, Convert.ToInt32(ConfigurationManager.AppSettings["Servidor_porta"]));
            listener = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            try
            {
                Console.WriteLine("Start server " + DateTime.Now.ToString());
                SalvaArquivo("   <------   Start server " + DateTime.Now.ToString() + "    ------>");
                listener.Bind(localEndPoint);
                listener.Listen(999);

                while (true)
                {
                    allDone.Reset();
                    listener.BeginAccept(new AsyncCallback(AsyncCallback), null);
                    allDone.WaitOne();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("Houve um erro ao iniciar as " + DateTime.Now.ToString());
                SalvaArquivo(ex.Message);
            }
        }


        private static void AsyncCallback(IAsyncResult ar)
        {
            try
            {
                allDone.Set();
                Socket handler = listener.EndAccept(ar);
                handler.BeginReceive(bytes, 0, bytes.Length, 0, new AsyncCallback(ReadCallback), handler);
                listener.BeginAccept(new AsyncCallback(AsyncCallback), null);
            }
            catch (Exception)
            {
                throw;
            }
        }


        private static void ReadCallback(IAsyncResult ar)
        {
            Program obj = new Program();
            string strErro = string.Empty;

            try
            {
                DadosVeiculoDto dto = new DadosVeiculoDto();
                Socket handler = (Socket)ar.AsyncState;

                if (handler.Connected)
                {
                    int bytesRead = handler.EndReceive(ar);
                    StringBuilder sb = new StringBuilder();

                    if (bytesRead > 1)
                    {
                        sb.Append(Encoding.UTF8.GetString(bytes, 0, bytesRead));

                        strErro = sb.ToString();

                        Console.WriteLine("\nA new connection " + DateTime.Now.ToString() + "\n");
                        Console.WriteLine(sb.ToString());
                        SalvaArquivo(sb.ToString());

                        var resposta = sb.ToString().Split(new char[] { ':' });

                        if (resposta.Length == 2)
                        {
                            var comando = resposta[1].Split(new char[] { ',' });

                            if (comando.Length > 0)
                            {
                                switch (resposta[0].Trim())
                                {
                                    case "+RESP":
                                        switch (comando[0])
                                        {
                                            case "GTFRI":
                                                dto.IMEI = comando[2];
                                                dto.speed = comando[8];
                                                dto.altidude = comando[10];
                                                dto.longitude = comando[11];
                                                dto.latitude = comando[12];
                                                dto.dataDevice = comando[13];
                                                dto.data = DateTime.Now;
                                                obj.dadosVeiculos.Cadastrar(dto);
                                                Command(obj, handler, dto.IMEI);
                                                obj.dadosVeiculos.Dispose();
                                                handler.Disconnect(true);
                                                return;
                                            case "GTIGN":
                                            case "GTIGF":
                                                dto.IMEI = comando[2];
                                                dto.speed = comando[6];
                                                dto.altidude = comando[8];
                                                dto.longitude = comando[9];
                                                dto.latitude = comando[10];
                                                dto.dataDevice = comando[11];
                                                dto.data = DateTime.Now;
                                                obj.dadosVeiculos.Cadastrar(dto);
                                                Command(obj, handler, dto.IMEI);
                                                obj.dadosVeiculos.Dispose();
                                                handler.Disconnect(true);
                                                var ignicao = Mapper.Map<Veiculo, VeiculoDto>(obj.veiculos.GetVeiculo(dto.IMEI));                                     
                                                if (ignicao != null)
                                                {
                                                    ignicao.ignicao = (comando[0] == "GTIGN" ? true : false);                                          
                                                    obj.veiculos.Alterar(ignicao);
                                                }
                                                return;                                            
                                        }
                                        break;
                                    case "+BUFF":
                                        switch (comando[0])
                                        {
                                            case "GTFRI":
                                                dto.IMEI = comando[2];
                                                dto.speed = comando[8];
                                                dto.altidude = comando[10];
                                                dto.longitude = comando[11];
                                                dto.latitude = comando[12];
                                                dto.dataDevice = comando[13];
                                                if (comando[13] != "")
                                                {
                                                    dto.data = Convert.ToDateTime(comando[13].Substring(0, 4) + "-" + comando[13].Substring(4, 2) + "-" + comando[13].Substring(6, 2) + " " + comando[13].Substring(8, 2) +":"+comando[13].Substring(10, 2));
                                                }
                                                if(dto.data < DateTime.Now)
                                                {
                                                    obj.dadosVeiculos.Cadastrar(dto);
                                                    Command(obj, handler, dto.IMEI);
                                                    obj.dadosVeiculos.Dispose();                                                  
                                                }
                                                handler.Disconnect(true);
                                                return;
                                        }
                                        break;
                                    case "+ACK":
                                        switch (comando[0])
                                        {
                                            case "GTOUT":

                                                var bloqueio = Mapper.Map<Veiculo, VeiculoDto>(obj.veiculos.GetVeiculo(comando[2]));

                                                if (bloqueio != null)
                                                {
                                                    bloqueio.avisoBloqueio = true;
                                                    bloqueio.comandoBloqueo = false;
                                                    bloqueio.bloqueado = (comando[4] == "0000" ? true : false);
                                                    obj.veiculos.Alterar(bloqueio);

                                                    MensagemDto mensagem = new MensagemDto();
                                                    mensagem.cpf = bloqueio.Cpf;
                                                    mensagem.fl_lida = false;
                                                    mensagem.ds_mensagem = "Veiculo com placa: " + bloqueio.ds_placa + ", foi " + (comando[4] == "0000" ? "bloqueado" : "desbloqueado") + " com sucesso!";
                                                    mensagem.dt_mensagem = DateTime.Now;
                                                    mensagem.id_tipo_Mensagem = (comando[4] == "0000" ? 2: 1);
                                                    obj.mensagem.Cadastrar(mensagem);

                                                }

                                                break;
                                        }

                                    break;
                                }
                            }
                            else
                            {
                                obj.dadosVeiculos.Dispose();
                                handler.Close();
                                return;
                            }

                            obj.dadosVeiculos.Dispose();
                        }
                        else
                        {
                            obj.dadosVeiculos.Dispose();
                            handler.Close();
                            return;
                        }

                        handler.BeginReceive(bytes, 0, bytes.Length, SocketFlags.None, new AsyncCallback(ReadCallback), handler);
                    }
                    else
                    {
                        obj.dadosVeiculos.Dispose();
                        handler.Close();
                        return;
                    }
                }
                else
                {
                    obj.dadosVeiculos.Dispose();
                    handler.Close();
                    return;
                }

            }
            catch (Exception ex)
            {
                var time = DateTime.Now.ToString();
                obj.dadosVeiculos.Dispose();
                Console.WriteLine("Houve um Erro ao receber as informacõss, as: " + time);
                SalvaArquivo(time + "  " + ex.Message + " ---> " + strErro);
                return;
            }
        }


        private static void Send(Socket handler, String data)
        {
            byte[] byteData = Encoding.ASCII.GetBytes(data);

            handler.BeginSend(byteData, 0, byteData.Length, 0, new AsyncCallback(SendCallback), handler);
        }


        private static void SendCallback(IAsyncResult ar)
        {

        }


        private static void Command(Program obj, Socket handler, string IMEI)
        {
            try
            {
                var DtoVeiculo = obj.veiculos.GetVeiculo(IMEI);

                if (DtoVeiculo == null)
                    return;

                if (DtoVeiculo.comandoBloqueo == true)
                {
                    string bit = string.Empty;

                    switch (DtoVeiculo.bloqueado)
                    {
                        case true:
                            bit = "1";
                            break;

                        case false:
                            bit = "0";
                            break;
                    }


                    if (DtoVeiculo.Rastreador != null)
                    {
                        switch (DtoVeiculo.Rastreador.ds_rastreador)
                        {
                            case "GMT200":
                                Send(handler, "AT+GTOUT=" + DtoVeiculo.Rastreador.ds_senha + "," + bit + ",0,0,0,,,,,,,,,,000" + bit + "$");
                                break;

                            case "GV300":
                                Send(handler, "AT+GTOUT=" + DtoVeiculo.Rastreador.ds_senha + "," + bit + ",,,0,0,0,0,5,1,0,,1,1,,,,000" + bit + "$ ");
                                break;

                            case "GV50":
                                Send(handler, "AT+GTOUT=" + DtoVeiculo.Rastreador.ds_senha + "," + bit + ",,,,,,0,,,,,,,000" + bit + "$");
                                break;
                        }
                    }
                    else
                    {
                        var time = DateTime.Now.ToString();
                        obj.dadosVeiculos.Dispose();
                        Console.WriteLine("Modelo de rastreador não encontrado: " + time);
                        SalvaArquivo(time + " Modelo de rastreador não encontrado");
                        handler.Disconnect(true); 
                        return;
                    }              
                }
            }
            catch (Exception ex)
            {
                var time = DateTime.Now.ToString();
                obj.dadosVeiculos.Dispose();
                Console.WriteLine("Houve um Erro ao enviar um comando, as: " + time);
                SalvaArquivo( time +"  "+ ex.Message);
                handler.Disconnect(true); 
            }
        }

        private static void SalvaArquivo(string texto)
        {
            FileStream fs = new FileStream(ConfigurationManager.AppSettings["Caminholog"].ToString(), FileMode.Append);
            StreamWriter writer = new StreamWriter(fs, Encoding.UTF8);
            writer.WriteLine(texto);

            writer.Flush();
            writer.Close();
            fs.Close();
        }
    }
}

