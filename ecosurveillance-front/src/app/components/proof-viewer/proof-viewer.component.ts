// import { Component, Input, Output, EventEmitter } from '@angular/core';
// import { CommonModule } from '@angular/common';

// interface Proof {
//   type: 'image' | 'video';
//   url: string;
// }

// @Component({
//   selector: 'app-proof-viewer',
//   standalone: true,
//   imports: [CommonModule],
//   templateUrl: './proof-viewer.component.html',
//   styleUrls: ['./proof-viewer.component.css']
// })
// export class ProofViewerComponent {
//   // Infraction sélectionnée
//   @Input() infractionId!: number; // <-- attention ! ne pas mettre | null ici
//   @Output() closeEvent = new EventEmitter<void>();

//   selectedProof: Proof | null = null;

//   proofs: Proof[] = [];

//   ngOnChanges() {
//     if (this.infractionId) {
//       // Simuler récupération des preuves depuis l'infraction
//       this.proofs = [
//         { type: 'image', url: 'assets/proof1.jpg' },
//         { type: 'video', url: 'assets/proof2.mp4' }
//       ];
//       this.selectedProof = null;
//     }
//   }

//   openPreview(proof: Proof) {
//     this.selectedProof = proof;
//   }

//   closePreview() {
//     this.selectedProof = null;
//     this.closeEvent.emit();
//   }
// }
// import { Component, Input, Output, EventEmitter, OnChanges } from '@angular/core';
// import { CommonModule } from '@angular/common';
// import { HttpClient } from '@angular/common/http';

// interface Proof {
//   type: 'image' | 'video';
//   url: string;
// }

// @Component({
//   selector: 'app-proof-viewer',
//   standalone: true,
//   imports: [CommonModule],
//   templateUrl: './proof-viewer.component.html',
//   styleUrls: ['./proof-viewer.component.css']
// })
// export class ProofViewerComponent implements OnChanges {

//   @Input() infractionId!: number;
//   @Output() closeEvent = new EventEmitter<void>();

//   proofs: Proof[] = [];
//   selectedProof: Proof | null = null;
//   loading = false;

//   private apiUrl = 'http://localhost:8081/api/preuves';

//   constructor(private http: HttpClient) {}

//   ngOnChanges(): void {
//     if (this.infractionId) {
//       this.chargerPreuves();
//     }
//   }

//   chargerPreuves(): void {
//     this.loading = true;
//     this.proofs = [];
//     this.http.get<any[]>(`${this.apiUrl}/${this.infractionId}`).subscribe({
//       next: (data) => {
//         data.forEach(p => {
//           if (p.photoUrl) this.proofs.push({ type: 'image', url: p.photoUrl });
//           if (p.videoUrl) this.proofs.push({ type: 'video', url: p.videoUrl });
//         });
//         this.loading = false;
//       },
//       error: () => { this.loading = false; }
//     });
//   }

//   openPreview(proof: Proof): void { this.selectedProof = proof; }

//   closePreview(): void {
//     this.selectedProof = null;
//     this.closeEvent.emit();
//   }
// }

import { Component, Input, Output, EventEmitter, OnChanges, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';

interface Proof {
  id?: number;
  type: 'image' | 'video';
  url: string;
  safeUrl?: SafeResourceUrl;
  photoUrl?: string;
  videoUrl?: string;
}

@Component({
  selector: 'app-proof-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './proof-viewer.component.html',
  styleUrls: ['./proof-viewer.component.css']
})
export class ProofViewerComponent implements OnChanges {

  @Input() infractionId!: number;
  @Output() closeEvent = new EventEmitter<void>();

  proofs: Proof[] = [];
  selectedProof: Proof | null = null;
  loading = false;
  error: string | null = null;

  private apiUrl = 'http://localhost:8081/api/preuves';
  private mediaBaseUrl = 'http://localhost:8081';

  constructor(
    private http: HttpClient,
    private sanitizer: DomSanitizer
  ) {}

  ngOnChanges(): void {
    if (this.infractionId && this.infractionId > 0) {
      this.chargerPreuves();
    }
  }

  chargerPreuves(): void {
    this.loading = true;
    this.error = null;
    this.proofs = [];
    
    // Utiliser le bon endpoint avec /infraction/
    this.http.get<any[]>(`${this.apiUrl}/infraction/${this.infractionId}`).subscribe({
      next: (data) => {
        console.log('Preuves reçues:', data);
        
        if (!data || data.length === 0) {
          this.error = 'Aucune preuve disponible pour cette infraction.';
          this.loading = false;
          return;
        }
        
        data.forEach(p => {
          // Ajouter la photo si elle existe
          if (p.photoUrl && p.photoUrl !== '') {
            const fullUrl = p.photoUrl.startsWith('http') 
              ? p.photoUrl 
              : `${this.mediaBaseUrl}${p.photoUrl}`;
            
            this.proofs.push({
              id: p.id ? parseInt(p.id) : undefined,
              type: 'image',
              url: fullUrl,
              safeUrl: this.sanitizer.bypassSecurityTrustResourceUrl(fullUrl),
              photoUrl: p.photoUrl,
              videoUrl: p.videoUrl
            });
          }
          
          // Ajouter la vidéo si elle existe
          if (p.videoUrl && p.videoUrl !== '') {
            const fullUrl = p.videoUrl.startsWith('http') 
              ? p.videoUrl 
              : `${this.mediaBaseUrl}${p.videoUrl}`;
            
            this.proofs.push({
              id: p.id ? parseInt(p.id) : undefined,
              type: 'video',
              url: fullUrl,
              safeUrl: this.sanitizer.bypassSecurityTrustResourceUrl(fullUrl),
              photoUrl: p.photoUrl,
              videoUrl: p.videoUrl
            });
          }
        });
        
        this.loading = false;
        
        if (this.proofs.length === 0 && !this.error) {
          this.error = 'Aucun fichier média trouvé pour cette infraction.';
        }
      },
      error: (err) => {
        console.error('Erreur lors du chargement des preuves:', err);
        this.error = 'Erreur lors du chargement des preuves. Veuillez réessayer.';
        this.loading = false;
      }
    });
  }

  openPreview(proof: Proof): void { 
    this.selectedProof = proof; 
  }

  closePreview(): void {
    this.selectedProof = null;
    this.closeEvent.emit();
  }
  
  closeModal(): void {
    this.closeEvent.emit();
  }
  
  
  reloadPreuves(): void {
    this.chargerPreuves();
  }
}