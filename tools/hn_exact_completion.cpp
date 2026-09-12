#include <bits/stdc++.h>
using namespace std;
using i64 = long long;
using i128 = __int128_t;
using V = array<i64,8>;
static const V CORR = {-1,-1,0,1,1,1,0,-1};

static V vmul64(const V&a,const V&b){
    array<i128,15> p{};
    for(int i=0;i<8;i++) if(a[i]) for(int j=0;j<8;j++) if(b[j]) p[i+j]+=(i128)a[i]*b[j];
    for(int d=14;d>=8;--d){i128 c=p[d]; if(c){p[d]=0; for(int i=0;i<8;i++) p[d-8+i]+=c*CORR[i];}}
    V r{}; for(int i=0;i<8;i++){ if(p[i] > LLONG_MAX || p[i] < LLONG_MIN){cerr<<"overflow\n"; exit(4);} r[i]=(i64)p[i]; }
    return r;
}
static vector<V> zpows(){
    vector<V>P(30);P[0][0]=1;
    for(int k=0;k<29;k++){
        array<i128,9>w{}; for(int i=0;i<8;i++)w[i+1]=P[k][i]; i128 c=w[8];
        for(int i=0;i<8;i++) w[i]+=c*CORR[i];
        for(int i=0;i<8;i++) P[k+1][i]=(i64)w[i];
    }
    return P;
}
static vector<V> ZP=zpows();
static array<V,8> CONJ=[](){array<V,8>x{};x[0]=ZP[0];for(int i=1;i<8;i++)x[i]=ZP[30-i];return x;}();
static V vconj(const V&a){V o{};for(int i=0;i<8;i++) if(a[i]) for(int j=0;j<8;j++) o[j]+=a[i]*CONJ[i][j];return o;}
struct P { V a{},b{}; i64 d; };
static bool unitdiff(const P&p,const P&q){
    V A{},B{}; i64 den=p.d*q.d;
    for(int i=0;i<8;i++){A[i]=p.a[i]*q.d-q.a[i]*p.d; B[i]=p.b[i]*q.d-q.b[i]*p.d;}
    V Ac=vconj(A), Bc=vconj(B);
    V aa=vmul64(A,Ac), bb=vmul64(B,Bc), ab=vmul64(A,Bc), ba=vmul64(B,Ac);
    i128 den2=(i128)den*den;
    for(int i=0;i<8;i++){
        i128 real=(i128)aa[i]+11*(i128)bb[i];
        i128 imag=-(i128)ab[i]+(i128)ba[i];
        if(imag!=0) return false;
        i128 want=(i==0?den2:0);
        if(real!=want) return false;
    }
    return true;
}
// Input: n, then for each point: den a[0..7] b[0..7].
int main(){ios::sync_with_stdio(false);cin.tie(nullptr);
    int n; if(!(cin>>n))return 1; vector<P> pts(n); for(auto &p:pts){cin>>p.d;for(auto &x:p.a)cin>>x;for(auto &x:p.b)cin>>x;}
    long long count=0; for(int i=0;i<n;i++){for(int j=i+1;j<n;j++) if(unitdiff(pts[i],pts[j])){cout<<i<<" "<<j<<"\n";count++;} if(i%200==0) cerr<<"i="<<i<<" edges="<<count<<"\n";}
    cerr<<"DONE edges="<<count<<"\n";
}
