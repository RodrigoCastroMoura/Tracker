using System;
using System.Collections.Generic;
using System.Linq;
using FluentValidation;
using RastreioFacil.Domain.DTO;
using MongoDB.Bson.Serialization.Attributes;
using MongoDB.Bson;

namespace RastreioFacil.Domain.Entities
{
    public class Veiculo
    {
        [BsonRepresentation(BsonType.ObjectId)]
        public string _id { get; private set; }  

        public string IMEI  { get; private set; }
        
        public string Cpf  { get; private set; }      
	    
        public int? id_marca  { get; private set; }            
	    
        public string id_rastreador  { get; private set; }       
	    
        public int? id_status  { get; private set; }           
	    
        public string ds_placa  { get; private set; }             
	    
        public string ds_modelo  { get; private set; }
        
        public int? nm_ano { get; private set; }  
	    
        public int? nm_modelo   { get; private set; }        
        
        public string nm_chip { get; private set; }         
	      
        public bool? avisoBloqueio { get; private set; }       
	    
        public bool? comandoBloqueo { get; private set; }     
	    
        public bool? bloqueado { get; private set; }

        public bool? auxBloqueado { get; private set; } 
	    
        public bool? comandoTempo { get; private set; }   
	    
        public string tempoIgnicaoON { get; private set; }         
	    
        public string tempoIgnicaoOFF { get; private set; }

        public bool ignicao { get; private set; }
        
        public string cd_user_cadm { get; private set; }    
	    
        public DateTime? ts_user_cadm { get; private set; }                           
	    
        public string cd_user_manu { get; private set; }           
	    
        public DateTime? ts_user_manu { get; private set; }

        public virtual Cliente Cliente { get;  set; }

        public virtual Rastreador Rastreador { get;  set; }

        public virtual MarcaVeiculo MarcaVeiculo { get;  set; }

        public virtual StatusVeiculo StatusVeiculo { get;  set; }

        public virtual IEnumerable<Mensagem> Mensagem { get; set; }

        public virtual IEnumerable<DadosVeiculo> DadosVeiculo { get; set; }

        public virtual IEnumerable<LogPagamento> LogPagamento { get; set; }

        public void DadosVeiculoDataEspecifica(DateTime? dataEspecifica)
        {
           
        }
     
        protected Veiculo()
        {
            DadosVeiculo = new HashSet<DadosVeiculo>();
            LogPagamento = new HashSet<LogPagamento>();
        }

        private Veiculo(VeiculoDto veiculoDto)
        {
            this._id = veiculoDto._id;
            this.IMEI = veiculoDto.IMEI  ;
            this.Cpf = veiculoDto.Cpf  ;
            this.id_marca = veiculoDto.id_marca  ;
            this.id_rastreador = veiculoDto.id_rastreador  ;
            this.id_status = veiculoDto.id_status  ;
            this.ds_placa = veiculoDto.ds_placa  ;
            this.ds_modelo = veiculoDto.ds_modelo  ;
            this.nm_ano = veiculoDto.nm_ano  ;
            this.nm_modelo = veiculoDto.nm_modelo  ;
            this.nm_chip = veiculoDto.nm_chip;
            this.avisoBloqueio = veiculoDto.avisoBloqueio ;
            this.auxBloqueado = veiculoDto.auxBloqueado;
            this.comandoBloqueo = veiculoDto.comandoBloqueo  ;
            this.bloqueado = veiculoDto.bloqueado  ;
            this.comandoTempo = veiculoDto.comandoTempo  ;
            this.tempoIgnicaoON = veiculoDto.tempoIgnicaoON  ;
            this.tempoIgnicaoOFF = veiculoDto.tempoIgnicaoOFF  ;
            this.ignicao = veiculoDto.ignicao;
            this.cd_user_cadm = veiculoDto.cd_user_cadm  ;
            this.ts_user_cadm = veiculoDto.ts_user_cadm;
            this.cd_user_manu = veiculoDto.cd_user_manu  ;
            this.ts_user_manu = DateTime.Now;        
        }

        public static Veiculo RetornoVeiculo(VeiculoDto veiculoDto)
        {
            return new Veiculo(veiculoDto);
        }

    }
}
