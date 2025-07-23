using FluentValidation;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using RastreioFacil.Domain.DTO;
using System;
using System.Collections.Generic;


namespace RastreioFacil.Domain.Entities
{
    public class DadosVeiculo
    {
        [BsonRepresentation(BsonType.ObjectId)]
        public string _id { get; set; }             
	    public string IMEI   { get;  set; }                    
	    public string longitude  { get;  set; }                   
	    public string latitude   { get;  set; }                    
	    public string altidude   { get;  set; }                    
	    public string speed      { get;  set; }                    
	    public bool? ignicao    { get;  set; }                    
	    public DateTime? data     { get;  set; }                      
	    public string dataDevice      { get;  set; }

        public virtual Veiculo Veiculo { get;  set; }
    
        protected DadosVeiculo()
        {
             
        }

        private DadosVeiculo(DadosVeiculoDto dadosVeiculo)
        {
            this._id = dadosVeiculo._id;
            this.IMEI = dadosVeiculo.IMEI;
            this.longitude = dadosVeiculo.longitude;
            this.latitude = dadosVeiculo.latitude;
            this.altidude = dadosVeiculo.altidude;
            this.speed = dadosVeiculo.speed;
            this.ignicao = dadosVeiculo.ignicao;
            this.data = dadosVeiculo.data;
            this.dataDevice = dadosVeiculo.dataDevice;
        }


        public static DadosVeiculo RetornoDadosVeiculos(DadosVeiculoDto dadosVeiculosDto)
        {
            return new DadosVeiculo(dadosVeiculosDto);
        }

    }
}
