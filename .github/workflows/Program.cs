using System;

public class Ejercicio22
{
    public static void Main()
    {
        int numero, resultado, divisorActual = 1, divisores = 0, numero2 = 0, divisorActual2 = 1, divisores2 = 0;

        Console.Write("Ingrese el primer número entero: ");
        numero = Convert.ToInt32(Console.ReadLine());

        Console.Write("Ingrese el segundo número entero: ");//forzar para que sea mayor a *numero
        numero2 = Convert.ToInt32(Console.ReadLine());

        while (numero > numero2)
        {
            Console.Write("El segundo numero debe ser mayor al primer numero. Ingrese el segundo número entero: ");//forzar para que sea mayor a *numero
            numero2 = Convert.ToInt32(Console.ReadLine());
        }
        while (divisorActual <= numero)
        {
            if (numero % divisorActual == 0)
            {
                divisores++;
            }

            if (divisorActual == numero)
            {
                if (divisores == 2)
                {
                    //Nada
                }
                else
                {
                    divisorActual = 0;
                    divisores = 0;
                    numero++;
                }
            }
            divisorActual++;

            while (divisorActual2 <= numero2)
            {
                if (numero2 % divisorActual2 == 0)
                {
                    divisores2++;
                }

                if (divisorActual2 == numero2)
                {
                    if (divisores2 == 2)
                    {
                        //Nada
                    }
                    else
                    {
                        divisorActual2 = 0;
                        divisores2 = 0;
                        numero2--;
                    }
                }
                divisorActual2++;
            }
        }

        resultado = numero2 - numero;

        if (resultado < 0)
            Console.WriteLine("No hay numeros primos en la serie");
        else
        {
            Console.WriteLine("El menor numero primo de la serie es = {0}", numero);
            Console.WriteLine("El mayor numero primo de la serie es = {0}", numero2);
            Console.WriteLine("El resultado de la resta entre los numeros primos es = {0}", resultado);
        }
    }
}
