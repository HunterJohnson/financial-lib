/**********************************************************************************
Black Derman Toy short rate 
Binomial Lattice.  Risk neutral probabilities are taken to be 0.5.
Fitted to Yield-Curve data only.  (contstant volatility.)
**********************************************************************************/
#include <iostream>
#include <math.h>
#include <map>
#include<vector>
using namespace std;
double newton(int i, double x, double p, vector<double> q);
double f(double x,int i, double p, vector<double> q);
int main()
{
    int N=4;
    double T=4.0;                            //expiry
    double dt=T/N;
    double sigma=0.1;
    double rate[N+1];
        for(int i=0;i<=N;i++)
            rate[i]=0.05;                    //(flat) yield curve
    double U[N+1];
    U[0]=rate[0];
    double P[N+1];                        //pure discount bond prices
    for(int i=0;i<=N;i++)
        {
            P[i]=pow((1/(1+rate[i]*dt)),i*dt);
        }
    map<int,double> Q[N+1];            //state prices
    map<int,double> r[N+1];            //interest rates
    map<int,double> d[N+1];            //bond prices
    r[0][0]=rate[0];
    d[0][0]=1/(1+r[0][0]*dt);
    Q[0][0]=1.0;
    for(int i=1;i<=N;i++)
        {
            for(int j=-i;j<=i;j=j+2)
                {      
//first calculate the state prices
                    if(j==i)
                        {Q[i][i]= 0.5*Q[i-1][i-1]*d[i-1][i-1];}
                    if(j==-i)
                        {Q[i][-i]=0.5*Q[i-1][-i+1]*d[i-1][-i+1];}
 
                    Q[i][j]=0.5*(Q[i-1][j-1]*d[i-1][j-1]+Q[i-1][j+1]*d[i-1][j+1]);
                }//j
//use bond price data to solve for the function U(i)
            vector<double> q(i+1);
            double p = P[i+1];
            for(int j=0;j<=i;j++)
                {
                    int k =-i+(2*j);
                    q[j]=Q[i][k];
                }
            U[i]=newton(i,0.1,p,q);
            for(int j=-i;j<=i;j=j+2)
                {
                    r[i][j]=U[i]*exp(sigma*j*sqrt(dt));
                    d[i][j]=1/(1+r[i][j]*dt);
                }//j
 
        }//i
return 0;
}
//functions implementing newton-raphson method to find function U(i)
double f(double x,int i, double p,const vector<double> q)
{
    double sigma = 0.1;
    int N=4;
    double T=4.0;
    double dt=T/N;
    double fx=0;
    for(int j=0;j<=i;j++)
        {
            //int k = -i+(2*j);
            fx+= q[j]*1/(1+x*exp(sigma*(-i+(2*j))*sqrt(dt))*dt);
        }
    fx = fx-p;
return fx;
}
double newton(int i, double x, double p,const vector<double> q)
{
//p=bond price
//j=number of nodes at the timestep
//x=intitial guess
//q = state price
    double D;
    double h=0.01;
    double T = 0.001;                //error tolerance
            if (x > 1.0 || x < -1.0)
                h=0.01*x;
            D = (2*h*f(x,i,p,q))/(f(x+h,i,p,q)-f(x-h,i,p,q));
            x = x-D;
    while (abs(D)>T)
        {
            if (x > 1.0 || x < -1.0)
                h=0.01*x;
            D = 2*h*f(x,i,p,q)/(f(x+h,i,p,q)-f(x-h,i,p,q));
            x = x-D;
        }
return x;
}
