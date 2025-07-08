import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LoginAuthComponent } from './auth';

describe('Auth', () => {
  let component: LoginAuthComponent;
  let fixture: ComponentFixture<LoginAuthComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LoginAuthComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(LoginAuthComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
