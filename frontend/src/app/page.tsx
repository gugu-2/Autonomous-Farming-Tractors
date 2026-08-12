"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Activity, Battery, ShieldAlert, Cpu, Camera, MapPin, Gauge } from "lucide-react";

export default function Dashboard() {
  const [telemetry, setTelemetry] = useState({
    battery: 87,
    cpu: 45,
    memory: 62,
    speed: 0.0,
    health: "NOMINAL",
    lat: 37.7749,
    lng: -122.4194
  });

  const [activeMachines, setActiveMachines] = useState([
    { id: "TRACTOR-01", status: "ACTIVE", task: "Plowing Field A", battery: 87 },
    { id: "COMBINE-02", status: "CHARGING", task: "Idle", battery: 20 },
    { id: "SPRAYER-03", status: "OFFLINE", task: "Maintenance", battery: 0 },
    { id: "EXCAVATOR-01", status: "ACTIVE", task: "Trenching", battery: 92 },
  ]);

  // Simulate incoming telemetry data
  useEffect(() => {
    const interval = setInterval(() => {
      setTelemetry((prev) => ({
        ...prev,
        battery: Math.max(0, prev.battery - (Math.random() > 0.8 ? 1 : 0)),
        cpu: Math.floor(30 + Math.random() * 40),
        memory: Math.floor(50 + Math.random() * 30),
        speed: prev.health === "E-STOP" ? 0.0 : +(Math.random() * 5).toFixed(1)
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const triggerEStop = () => {
    setTelemetry(prev => ({ ...prev, health: "E-STOP", speed: 0.0 }));
    setActiveMachines(prev => prev.map(m => ({ ...m, status: "HALTED" })));
  };

  return (
    <div className="min-h-screen bg-background p-6 font-sans text-foreground">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 pb-4 border-b border-border/40">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-primary flex items-center gap-3">
            <Cpu className="h-8 w-8" />
            AGRO-AI OMNIDRIVE
          </h1>
          <p className="text-muted-foreground mt-1 text-sm tracking-widest uppercase">Fleet Management Subsystem</p>
        </div>
        <div className="flex gap-4 items-center">
          <Badge variant={telemetry.health === "NOMINAL" ? "default" : "destructive"} className="text-lg py-1 px-4">
            {telemetry.health === "NOMINAL" ? "SYSTEM NOMINAL" : "EMERGENCY HALT"}
          </Badge>
          
          <AlertDialog>
            <AlertDialogTrigger render={
              <Button variant="destructive" size="lg" className="font-bold tracking-widest shadow-lg shadow-destructive/20 animate-pulse" />
            }>
                <ShieldAlert className="mr-2 h-5 w-5" /> E-STOP ALL
            </AlertDialogTrigger>
            <AlertDialogContent className="border-destructive/50 bg-background/95 backdrop-blur-xl">
              <AlertDialogHeader>
                <AlertDialogTitle className="text-destructive text-2xl">Confirm Emergency Stop</AlertDialogTitle>
                <AlertDialogDescription className="text-lg">
                  This action will immediately halt all active autonomous machinery, engaging safety brakes and killing engine power. This cannot be undone remotely.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={triggerEStop} className="bg-destructive hover:bg-destructive/90 text-destructive-foreground font-bold">
                  ENGAGE E-STOP
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Col - Visuals & Camera */}
        <div className="col-span-1 lg:col-span-2 space-y-6">
          <Card className="border-primary/20 shadow-xl shadow-primary/5 bg-card/50 backdrop-blur-sm overflow-hidden">
            <CardHeader className="bg-primary/10 border-b border-primary/20 pb-3">
              <CardTitle className="flex items-center gap-2 text-primary">
                <Camera className="h-5 w-5" /> Multi-Spectral Vision Stream
              </CardTitle>
              <CardDescription>Live semantic segmentation feed from TRACTOR-01</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="aspect-video bg-black/80 flex items-center justify-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-primary/5 mix-blend-overlay"></div>
                
                {/* Mock Vision Boxes */}
                <div className="absolute border-2 border-primary/50 w-32 h-32 top-1/4 left-1/4 rounded-sm animate-pulse flex items-start justify-start p-1">
                  <span className="bg-primary/50 text-xs text-white px-1 rounded-sm">CROP (98%)</span>
                </div>
                <div className="absolute border-2 border-destructive/50 w-24 h-24 bottom-1/4 right-1/3 rounded-sm animate-pulse flex items-start justify-start p-1">
                  <span className="bg-destructive/80 text-xs text-white px-1 rounded-sm">WEED (91%)</span>
                </div>

                <div className="text-muted-foreground flex flex-col items-center opacity-50 group-hover:opacity-10 transition-opacity">
                  <Camera className="h-12 w-12 mb-4" />
                  <p>Stream Active • 30 FPS</p>
                </div>
                
                {/* Crosshair Overlay */}
                <div className="absolute inset-0 pointer-events-none opacity-20 bg-[linear-gradient(rgba(255,255,255,0.1)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.1)_1px,transparent_1px)] bg-[size:50px_50px]" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/30 backdrop-blur">
            <CardHeader>
              <CardTitle>Fleet Manifest</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow className="border-border/50 hover:bg-transparent">
                    <TableHead>Machine ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Current Task</TableHead>
                    <TableHead className="text-right">Battery</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {activeMachines.map((machine) => (
                    <TableRow key={machine.id} className="border-border/20">
                      <TableCell className="font-mono font-medium">{machine.id}</TableCell>
                      <TableCell>
                        <Badge variant={
                          machine.status === 'ACTIVE' ? 'default' : 
                          machine.status === 'HALTED' ? 'destructive' : 'secondary'
                        }>
                          {machine.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{machine.task}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Progress value={machine.battery} className="w-16 h-2" />
                          <span className="text-xs">{machine.battery}%</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Right Col - Telemetry */}
        <div className="space-y-6">
          <Card className="border-border/50 bg-card/30 backdrop-blur">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" /> Live Telemetry
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2 text-muted-foreground"><Battery className="h-4 w-4"/> HV Battery Pack</span>
                  <span className="font-mono">{telemetry.battery}%</span>
                </div>
                <Progress value={telemetry.battery} className="h-2" />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2 text-muted-foreground"><Cpu className="h-4 w-4"/> AI Brain CPU Load</span>
                  <span className="font-mono">{telemetry.cpu}%</span>
                </div>
                <Progress value={telemetry.cpu} className="h-2 [&>div]:bg-amber-500" />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2 text-muted-foreground"><Gauge className="h-4 w-4"/> Current Speed</span>
                  <span className="font-mono">{telemetry.speed} km/h</span>
                </div>
              </div>

              <div className="space-y-2 pt-4 border-t border-border/50">
                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2 text-muted-foreground"><MapPin className="h-4 w-4"/> GPS Latitude</span>
                  <span className="font-mono text-primary/80">{telemetry.lat.toFixed(6)}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2 text-muted-foreground"><MapPin className="h-4 w-4"/> GPS Longitude</span>
                  <span className="font-mono text-primary/80">{telemetry.lng.toFixed(6)}</span>
                </div>
              </div>

            </CardContent>
          </Card>

          <Card className="border-border/50 bg-card/30 backdrop-blur">
            <CardHeader>
              <CardTitle>Hardware Modules</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="actuators" className="w-full">
                <TabsList className="w-full grid grid-cols-2 bg-secondary/50">
                  <TabsTrigger value="actuators">Actuators</TabsTrigger>
                  <TabsTrigger value="sensors">Sensors</TabsTrigger>
                </TabsList>
                <TabsContent value="actuators" className="space-y-4 pt-4">
                  <div className="flex justify-between items-center p-3 rounded-md bg-secondary/30 border border-border/50">
                    <span className="font-medium">Steering Servo</span>
                    <Badge variant="outline" className="text-primary border-primary">OK</Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-md bg-secondary/30 border border-border/50">
                    <span className="font-medium">Brake Actuator</span>
                    <Badge variant="outline" className="text-primary border-primary">OK</Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-md bg-secondary/30 border border-border/50">
                    <span className="font-medium">Throttle PWM</span>
                    <Badge variant="outline" className="text-primary border-primary">OK</Badge>
                  </div>
                </TabsContent>
                <TabsContent value="sensors" className="space-y-4 pt-4">
                  <div className="flex justify-between items-center p-3 rounded-md bg-secondary/30 border border-border/50">
                    <span className="font-medium">Ouster LiDAR</span>
                    <Badge variant="outline" className="text-primary border-primary">OK</Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-md bg-secondary/30 border border-border/50">
                    <span className="font-medium">ZED2 Stereo</span>
                    <Badge variant="outline" className="text-primary border-primary">OK</Badge>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-md bg-secondary/30 border border-border/50">
                    <span className="font-medium">RTK GPS Base</span>
                    <Badge variant="outline" className="text-primary border-primary">OK</Badge>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
