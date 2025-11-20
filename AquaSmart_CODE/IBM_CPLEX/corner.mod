/*********************************************
 * OPL 22.1.1.0 Model
 * Author: David
 * Creation Date: May 14, 2025 at 7:16:16 PM
 *********************************************/

 // zonas sobre las que se decidiran los dias de razonamiento
 {int} Z = ...;
 // Dias del mes
 {int} D = ...;
 //Tipos de sectores
 {int} T = ...;
 
 // Parametros
 // Consumo de agua estimada el dia d ∈ D en la zona z ∈ Z por los sectores tipo t ∈ T
 float c[Z][D][T] = ...;
 // Capacidad maxima de consumo diaria de agua permitida
 float p = ...;
 //recoleccion de agua en el dia d ∈ D
 float r[D] = ...;
 // Nivel de los embalses al inicio de mes
 float n_0 = ...;
 // proporcionalidad de consumo del mes 
 float e = ...;
 // Numero de habitantes en la zona z ∈ Z
 float h[Z] = ... ;
 // Capacidad maxima de los embalses
 float m = ...;
 
 //Variables de desicion
 dvar boolean x[Z][D];
 dvar float+ n[D];
 dvar float+ nivel_porcentaje[D];
 
 // Funcion objetivo
 minimize sum(z in Z,d in D,t in T) c[z][d][t]* x[z][d];
 // minimiza el consumo de agua mediante la seleccion de dias de razonamiento de las 9 zonas de racionamiento elejidas
 
 //Restricciones
 subject to 
 {
 	forall(d in D)
 	  nivel_porcentaje[d] == (n[d] / m) * 100;
   // Restriccion de consumo maximo por dia
   forall(d in D)	
   	sum(z in Z,t in T) c[z][d][t]*x[z][d] <= p ;
  // actualizacion de nivel de embalses (para el dia 1, i.e. d = 0 el n_0 hace referencia al parametro de nivel al inicio del mes)
  forall(d in D)
  	(d == first(D) ? n_0 + r[d] - sum(z in Z, t in T) c[z][d][t]*x[z][d] == n[d] : n[d-1] + r[d] - sum(z in Z, t in T) c[z][d][t]*x[z][d] == n[d]);
  // Restriccion para evitar mas de 2 dias de razonamiento seguidos en un mismo sector
  forall(z in Z)
    forall(d in 0..7)
    	x[z][d] + x[z][d+1] + x[z][d+2] >= 1;
   
  // Minimo de agua vital promedio a lo largo del mes
  forall(z in Z)
  	sum(d in D) c[z][d][2] * x[z][d] >= 50 * 30 * h[z];
  
 // El sector comercial debe recibir al menos el e% del consumo esperado para no afectar en exceso su actividad economica.
  forall(z in Z)
   (sum(d in D) c[z][d][0] * x[z][d] >= e * sum(d in D) c[z][d][0]);
 // El sector industrial debe recibir al menos el e% del consumo esperado para no afectar en exceso su actividad economica. 
  forall(z in Z)
   (sum(d in D) c[z][d][1] * x[z][d] >= e * sum(d in D) c[z][d][1]);
 //Capacidad minima establecida de los embalses
  forall(d in D)
    n[d] >= 0.3957 * m;
    
 // capacidad maxima estructural de los embalses
  forall(d in D)
    n[d] <= m;
}


 execute{
	 writeln("Resultado de la optimizacin:");
	 writeln("Objetivo: ",cplex.getObjValue());
	 writeln("\nNivel de embalses por d a (n):");
	 for(var d in D)
	 	writeln("Dia ", d,": ", nivel_porcentaje[d],  "%");
	 writeln("\nRationing days by zone (x[z][d] = 0):");
	 for (var z in Z) {
	   write("Zona ", z, ": ");
	   for (var d in D)
	   	if (x[z][d] == 0)
	   		write(d, " ");
	   writeln();
	   }
 }