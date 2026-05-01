import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router'; // 1. Ajout de Router ici
import { UserService } from '../../../services/user.service';
import { AuthService } from '../../../services/auth.service'; 
@Component({
  selector: 'app-users',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './users.component.html',
  styleUrls: ['./users.component.css']
})
export class UsersComponent implements OnInit {

  users: any[] = [];
  selectedUser: any = null;
  adminUser: any = null;

  constructor(
    private userService: UserService,
    private router: Router,
    private authService: AuthService
  ) {}

  ngOnInit(): void {
    this.adminUser = this.authService.getCurrentUser();
    this.loadUsers();
  }

  /**
   * Logique de déconnexion
   */
  onLogout(): void {
    // Nettoyage des données de session
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    sessionStorage.clear();

    // Redirection vers la page de connexion
    this.router.navigate(['/login']);
  }

  loadUsers() {
    this.userService.getUsers().subscribe((res: any[]) => {
      this.users = res.filter(u => u.role === 'ETUDIANT');
    });
  }

  addUser() {
    this.selectedUser = null;
    // Logique pour ouvrir un formulaire d'ajout ici
  }

  editUser(user: any) {
    this.selectedUser = { ...user };
    // Logique pour ouvrir un formulaire d'édition ici
  }

  deleteUser(userId: number) {
    if (confirm('Voulez-vous vraiment supprimer cet utilisateur ?')) {
      this.userService.deleteUser(userId).subscribe(() => {
        this.users = this.users.filter(u => u.id !== userId);
      });
    }
  }

  onFormSaved() {
    this.selectedUser = null;
    this.loadUsers();
  }
}