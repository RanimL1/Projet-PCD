// import { Component } from '@angular/core';
// import { CommonModule } from '@angular/common';
// import { RouterModule, Router } from '@angular/router';
// import { ProofViewerComponent } from '../../../components/proof-viewer/proof-viewer.component';

// @Component({
//   selector: 'app-my-infractions',
//   standalone: true,
//   imports: [CommonModule, RouterModule, ProofViewerComponent],
//   templateUrl: './my-infractions.component.html',
//   styleUrls: ['./my-infractions.component.css']
// })
// export class MyInfractionsComponent {

//   // Liste des punitions disponibles pour l'admin
//   private punitionsDisponibles: string[] = [
//     'Nettoyage du jardin de la faculté',
//     'Arrosage des plantes ',
//     'Tri des déchets (1h)',
//     'Organisation de la bibliothèque',
//     'Vérification de l\'extinction des lumières'
//   ];

//   infractions = [
//     { id: 1, description: '-', date: new Date('2026-01-02'), punition: '-', status: 'En attente' },
//     { id: 2, description: '-', date: new Date('2026-01-06'), punition: '-', status: 'Terminé' },
//     { id: 3, description: '-', date: new Date('2026-01-06'), punition: '-', status: 'Terminé' }
//   ];

//   selectedInfractionId: number | null = null;

//   constructor(private router: Router) {}

//   /**
//    * Valide l'infraction et attribue une punition aléatoire
//    */
//   valider(infraction: any): void {
//     if (infraction.status === 'En attente') {
//       // 1. Mise à jour du statut
//       infraction.status = 'En cours';

//       // 2. Sélection aléatoire d'une punition
//       const randomIndex = Math.floor(Math.random() * this.punitionsDisponibles.length);
//       infraction.punition = this.punitionsDisponibles[randomIndex];

//       console.log(`Infraction ${infraction.id} validée avec la punition : ${infraction.punition}`);
//     }
//   }

//   /**
//    * Déconnexion
//    */
//   onLogout(): void {
//     localStorage.removeItem('token');
//     localStorage.removeItem('user');
//     sessionStorage.clear();
//     this.router.navigate(['/login']);
//   }

//   openProofs(id: number) {
//     this.selectedInfractionId = id;
//   }

//   closeModal() {
//     this.selectedInfractionId = null;
//   }

//   get showModal(): boolean {
//     return this.selectedInfractionId !== null;
//   }
// }

// import { Component, OnInit } from '@angular/core';
// import { CommonModule } from '@angular/common';
// import { RouterModule, Router } from '@angular/router';
// import { ProofViewerComponent } from '../../../components/proof-viewer/proof-viewer.component';
// import { InfractionService } from '../../../services/infraction.service';
// import { AuthService } from '../../../services/auth.service';
// import { Infraction } from '../../../models/infraction.model';

// @Component({
//   selector: 'app-my-infractions',
//   standalone: true,
//   imports: [CommonModule, RouterModule, ProofViewerComponent],
//   templateUrl: './my-infractions.component.html',
//   styleUrls: ['./my-infractions.component.css']
// })
// export class MyInfractionsComponent implements OnInit {

//   infractions: Infraction[] = [];
//   currentUser: any = null;
//   selectedInfractionId: number | null = null;
//   loading = true;
//   error: string | null = null;
//   user: any;

//   constructor(
//     private infractionService: InfractionService,
//     private authService: AuthService,
//     private router: Router
//   ) {}

//   ngOnInit(): void {
//     this.currentUser = this.authService.getCurrentUser();
//     this.user = this.authService.getCurrentUser();
//     this.loadInfractions();
//   }

//   loadInfractions(): void {
//     this.loading = true;
//     // Récupère l'id depuis le user stocké
//     const user = JSON.parse(localStorage.getItem('user') || '{}');
//     this.infractionService.getInfractionsByEtudiant(user.id).subscribe({
//       next: (res) => {
//         this.infractions = res;
//         this.loading = false;
//       },
//       error: () => {
//         this.error = 'Impossible de charger vos infractions';
//         this.loading = false;
//       }
//     });
//   }

//   valider(infraction: Infraction): void {
//     if (infraction.status === 'EN_ATTENTE') {
//       this.infractionService.updateStatus(infraction.id, 'VALIDEE').subscribe({
//         next: (updated) => {
//           const index = this.infractions.findIndex(i => i.id === infraction.id);
//           if (index !== -1) this.infractions[index] = updated;
//         }
//       });
//     }
//   }

//   onLogout(): void {
//     this.authService.logout();
//   }

//   openProofs(id: number) { this.selectedInfractionId = id; }
//   closeModal() { this.selectedInfractionId = null; }
//   get showModal(): boolean { return this.selectedInfractionId !== null; }
// }

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { ProofViewerComponent } from '../../../components/proof-viewer/proof-viewer.component';
import { InfractionService } from '../../../services/infraction.service';
import { AuthService } from '../../../services/auth.service';
import { Infraction } from '../../../models/infraction.model';
import { PreuveService, Preuve } from '../../../services/preuve.service';

@Component({
  selector: 'app-my-infractions',
  standalone: true,
  imports: [CommonModule, RouterModule, ProofViewerComponent],
  templateUrl: './my-infractions.component.html',
  styleUrls: ['./my-infractions.component.css']
})
export class MyInfractionsComponent implements OnInit {

  infractions: Infraction[] = [];
  currentUser: any = null;
  user: any;
  selectedInfractionId: number | null = null;
  selectedInfractionPreuves: Preuve[] = [];
  loading = true;
  error: string | null = null;

  constructor(
    private infractionService: InfractionService,
    private authService: AuthService,
    private preuveService: PreuveService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.getCurrentUser();
    this.user = this.authService.getCurrentUser();
    this.loadInfractions();
  }

  loadInfractions(): void {
    this.loading = true;
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    this.infractionService.getInfractionsByEtudiant(user.id).subscribe({
      next: (res) => {
        this.infractions = res.map(i => ({
          ...i,
          status: i.status.toUpperCase() as 'EN_ATTENTE' | 'EN_COURS' | 'TERMINEE'
        }));
        this.loading = false;
      },
      error: () => {
        this.error = 'Impossible de charger vos infractions';
        this.loading = false;
      }
    });
  }

  valider(infraction: Infraction): void {
    if (infraction.status === 'EN_ATTENTE') {
      // 1️⃣ Update immédiat côté frontend
      infraction.status = 'EN_COURS';

      // 2️⃣ Appel API pour sauvegarder
      this.infractionService.updateStatus(infraction.id, 'EN_COURS').subscribe({
        next: (updated) => {
          const index = this.infractions.findIndex(i => i.id === infraction.id);
          if (index !== -1) this.infractions[index] = updated;
        },
        error: (err) => {
          console.error('Erreur validation infraction:', err);
          infraction.status = 'EN_ATTENTE';
        }
      });
    }
  }

  openProofs(id: number): void {
    this.selectedInfractionId = id;
    this.loadPreuves(id);
  }

  loadPreuves(infractionId: number): void {
    this.preuveService.getPreuvesByInfraction(infractionId).subscribe({
      next: (preuves) => this.selectedInfractionPreuves = preuves,
      error: (err) => {
        console.error('Erreur chargement preuves:', err);
        this.selectedInfractionPreuves = [];
      }
    });
  }

  closeModal(): void {
    this.selectedInfractionId = null;
    this.selectedInfractionPreuves = [];
  }

  onLogout(): void {
    this.authService.logout();
  }

  get showModal(): boolean {
    return this.selectedInfractionId !== null;
  }
}
