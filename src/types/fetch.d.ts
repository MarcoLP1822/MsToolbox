// types/fetch.d.ts
// Augmenta l’interfaccia globale di lib.dom
declare global {
    interface RequestInit {
      /** Node 18+ streaming body flag */
      duplex?: "half" | "full";
    }
  }
  
  export {};
  